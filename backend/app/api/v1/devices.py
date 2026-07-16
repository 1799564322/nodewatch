import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select, text

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.agent_token import AgentToken
from app.models.audit_log import AuditLog
from app.models.device import Device
from app.schemas.device import (
    DeviceCreate,
    DashboardResponse,
    DeviceListResponse,
    DeviceResponse,
    DeviceUpdate,
    TokenResponse,
)
from app.services.devices import create_agent_token, get_device_or_404, list_devices
from app.models.metric import DeviceLatestMetric
from app.models.metric import DiskLatestMetric, MetricSample
from app.models.alert import AlertEvent
from app.schemas.metric import DiskResponse, HistoryPoint, HistoryResponse
from app.schemas.alert import MaintenanceRequest
from app.core.config import get_settings

router = APIRouter(prefix="/devices", tags=["devices"])
dashboard_router = APIRouter(tags=["dashboard"])


@router.get("/{device_id}/metrics/history", response_model=HistoryResponse)
def metric_history(
    device_id: uuid.UUID,
    session: DbSession,
    _: CurrentUser,
    from_time: datetime = Query(alias="from"),
    to_time: datetime = Query(alias="to"),
    resolution: str | None = Query(default=None, pattern="^(raw|5m|1h)$"),
) -> HistoryResponse:
    get_device_or_404(session, device_id)
    if from_time.tzinfo is None or to_time.tzinfo is None or from_time >= to_time:
        raise HTTPException(status_code=422, detail="时间范围必须是有效的 ISO 8601 UTC")
    duration = to_time - from_time
    if duration > timedelta(days=31):
        raise HTTPException(status_code=422, detail="单次历史查询不能超过 31 天")
    selected = resolution or ("raw" if duration <= timedelta(hours=6) else "5m" if duration <= timedelta(hours=48) else "1h")
    if selected == "raw":
        rows = session.execute(
            select(MetricSample).where(
                MetricSample.device_id == device_id,
                MetricSample.collected_at >= from_time,
                MetricSample.collected_at <= to_time,
            ).order_by(MetricSample.collected_at).limit(1501)
        ).scalars().all()
        if len(rows) > 1500:
            raise HTTPException(status_code=422, detail="原始数据超过 1500 点，请提高分辨率")
        points = [HistoryPoint.model_validate(row, from_attributes=True) for row in rows]
    else:
        interval = text("INTERVAL '5 minutes'" if selected == "5m" else "INTERVAL '1 hour'")
        bucket = func.date_bin(interval, MetricSample.collected_at, text("TIMESTAMPTZ '1970-01-01 UTC'"))
        rows = session.execute(
            select(
                bucket.label("collected_at"),
                func.avg(MetricSample.cpu_percent),
                func.avg(MetricSample.memory_percent),
                func.avg(MetricSample.root_disk_percent),
                func.avg(MetricSample.net_tx_bytes_per_sec),
                func.avg(MetricSample.net_rx_bytes_per_sec),
            ).where(
                MetricSample.device_id == device_id,
                MetricSample.collected_at >= from_time,
                MetricSample.collected_at <= to_time,
            ).group_by(bucket).order_by(bucket).limit(1500)
        )
        points = [HistoryPoint(collected_at=r[0], cpu_percent=float(r[1]), memory_percent=float(r[2]), root_disk_percent=float(r[3]) if r[3] is not None else None, net_tx_bytes_per_sec=int(r[4]), net_rx_bytes_per_sec=int(r[5])) for r in rows]
    return HistoryResponse(resolution=selected, points=points)


@router.get("/{device_id}/disks", response_model=list[DiskResponse])
def get_disks(device_id: uuid.UUID, session: DbSession, _: CurrentUser) -> list[DiskLatestMetric]:
    get_device_or_404(session, device_id)
    return list(session.scalars(select(DiskLatestMetric).where(DiskLatestMetric.device_id == device_id).order_by(DiskLatestMetric.mountpoint)))


@router.get("", response_model=DeviceListResponse)
def get_devices(
    session: DbSession,
    _: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> DeviceListResponse:
    items, total = list_devices(session, page, page_size)
    metrics = {
        item.device_id: item
        for item in session.scalars(
            select(DeviceLatestMetric).where(
                DeviceLatestMetric.device_id.in_([device.id for device in items])
            )
        )
    }
    responses = []
    cutoff = datetime.now(UTC) - timedelta(seconds=get_settings().offline_after_seconds)
    for device in items:
        response = DeviceResponse.model_validate(device)
        latest = metrics.get(device.id)
        if latest:
            response.cpu_percent = float(latest.cpu_percent)
            response.memory_percent = float(latest.memory_percent)
            response.root_disk_percent = (
                float(latest.root_disk_percent) if latest.root_disk_percent is not None else None
            )
            response.net_tx_bytes_per_sec = latest.net_tx_bytes_per_sec
            response.net_rx_bytes_per_sec = latest.net_rx_bytes_per_sec
        response.status = (
            "disabled" if not device.is_enabled else "online"
            if device.last_seen_at and device.last_seen_at >= cutoff else "offline"
        )
        responses.append(response)
    return DeviceListResponse(items=responses, total=total, page=page, page_size=page_size)


@dashboard_router.get("/dashboard", response_model=DashboardResponse)
def dashboard(session: DbSession, _: CurrentUser) -> DashboardResponse:
    devices = list(session.scalars(select(Device).where(Device.is_enabled.is_(True))))
    latest = list(session.scalars(select(DeviceLatestMetric)))
    by_id = {item.device_id: item for item in latest}

    def enriched(device: Device) -> DeviceResponse:
        result = DeviceResponse.model_validate(device)
        metric = by_id.get(device.id)
        if metric:
            result.cpu_percent = float(metric.cpu_percent)
            result.memory_percent = float(metric.memory_percent)
        cutoff = datetime.now(UTC) - timedelta(seconds=get_settings().offline_after_seconds)
        result.status = "online" if device.last_seen_at and device.last_seen_at >= cutoff else "offline"
        return result

    cutoff = datetime.now(UTC) - timedelta(seconds=get_settings().offline_after_seconds)
    online = [device for device in devices if device.last_seen_at and device.last_seen_at >= cutoff]
    metric_online = [device for device in online if device.id in by_id]
    top_cpu = sorted(metric_online, key=lambda d: by_id[d.id].cpu_percent, reverse=True)[:5]
    top_memory = sorted(metric_online, key=lambda d: by_id[d.id].memory_percent, reverse=True)[:5]
    return DashboardResponse(
        total_devices=len(devices),
        online_devices=len(online),
        offline_devices=len(devices) - len(online),
        firing_alerts=session.scalar(select(func.count()).select_from(AlertEvent).where(AlertEvent.resolved_at.is_(None))) or 0,
        alert_devices=session.scalar(select(func.count(func.distinct(AlertEvent.device_id))).where(AlertEvent.resolved_at.is_(None))) or 0,
        top_cpu=[enriched(device) for device in top_cpu],
        top_memory=[enriched(device) for device in top_memory],
    )


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, session: DbSession, admin: AdminUser) -> Device:
    device = Device(name=payload.name.strip())
    session.add(device)
    session.flush()
    session.add(AuditLog(user_id=admin.id, action="device.create", resource_type="device", resource_id=str(device.id)))
    session.commit()
    return device


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: uuid.UUID, session: DbSession, _: CurrentUser) -> DeviceResponse:
    device = get_device_or_404(session, device_id)
    result = DeviceResponse.model_validate(device)
    cutoff = datetime.now(UTC) - timedelta(seconds=get_settings().offline_after_seconds)
    result.status = (
        "disabled" if not device.is_enabled else "online"
        if device.last_seen_at and device.last_seen_at >= cutoff else "offline"
    )
    return result


@router.patch("/{device_id}", response_model=DeviceResponse)
def update_device(payload: DeviceUpdate, device_id: uuid.UUID, session: DbSession, _: AdminUser) -> Device:
    device = get_device_or_404(session, device_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(device, field, value.strip() if isinstance(value, str) else value)
    session.commit()
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def disable_device(device_id: uuid.UUID, session: DbSession, _: AdminUser) -> Response:
    device = get_device_or_404(session, device_id)
    device.is_enabled = False
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{device_id}/tokens", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def generate_token(device_id: uuid.UUID, session: DbSession, admin: AdminUser) -> TokenResponse:
    device = get_device_or_404(session, device_id)
    token, raw_token = create_agent_token(session, device, admin.id)
    session.commit()
    return TokenResponse(token=raw_token, token_id=token.id, token_prefix=token.token_prefix)


@router.post("/{device_id}/tokens/{token_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_token(device_id: uuid.UUID, token_id: uuid.UUID, session: DbSession, admin: AdminUser) -> Response:
    token = session.scalar(select(AgentToken).where(AgentToken.id == token_id, AgentToken.device_id == device_id))
    if token is None:
        get_device_or_404(session, device_id)
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    token.revoked_at = datetime.now(UTC)
    session.add(AuditLog(user_id=admin.id, action="agent_token.revoke", resource_type="device", resource_id=str(device_id), details={"token_id": str(token.id)}))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{device_id}/maintenance", response_model=DeviceResponse)
def start_maintenance(device_id: uuid.UUID, payload: MaintenanceRequest, session: DbSession, _: AdminUser) -> Device:
    device = get_device_or_404(session, device_id)
    if payload.until.tzinfo is None or payload.until <= datetime.now(UTC):
        raise HTTPException(status_code=422, detail="维护结束时间必须晚于当前时间")
    device.maintenance_until = payload.until
    session.commit()
    return device


@router.delete("/{device_id}/maintenance", status_code=status.HTTP_204_NO_CONTENT)
def stop_maintenance(device_id: uuid.UUID, session: DbSession, _: AdminUser) -> Response:
    device = get_device_or_404(session, device_id)
    device.maintenance_until = None
    session.commit()
    return Response(status_code=204)
