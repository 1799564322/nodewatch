from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.api.deps import DbSession
from app.core.config import get_settings
from app.models.device import Device
from app.schemas.device import (
    BootstrapRequest,
    BootstrapResponse,
    SystemInfoRequest,
    SystemInfoResponse,
)
from app.schemas.metric import MetricBatchRequest, MetricIngestResponse, MetricRequest
from app.services.devices import authenticate_agent_token
from app.services.metrics import ingest_metric

router = APIRouter(prefix="/agent", tags=["agent"])
AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]


def authenticated_device(session: DbSession, authorization: AuthorizationHeader) -> Device:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 Agent Token")
    raw_token = authorization.removeprefix("Bearer ").strip()
    _, device = authenticate_agent_token(session, raw_token)
    return device


@router.post("/bootstrap", response_model=BootstrapResponse)
def bootstrap(
    payload: BootstrapRequest,
    request: Request,
    session: DbSession,
    authorization: AuthorizationHeader = None,
) -> BootstrapResponse:
    device = authenticated_device(session, authorization)
    if device.agent_instance_id not in (None, payload.agent_instance_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token 已绑定其他 Agent")
    device.agent_instance_id = payload.agent_instance_id
    device.agent_version = payload.agent_version
    device.hostname = payload.hostname
    device.last_seen_at = datetime.now(UTC)
    device.last_ip = request.client.host if request.client else None
    session.commit()
    settings = get_settings()
    return BootstrapResponse(
        device_id=device.id,
        collect_interval_seconds=settings.default_collect_interval_seconds,
        max_batch_samples=settings.max_agent_batch_samples,
        server_time=datetime.now(UTC),
    )


@router.post("/system-info", response_model=SystemInfoResponse)
def system_info(
    payload: SystemInfoRequest,
    request: Request,
    session: DbSession,
    authorization: AuthorizationHeader = None,
) -> SystemInfoResponse:
    device = authenticated_device(session, authorization)
    if device.agent_instance_id != payload.agent_instance_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent 实例与绑定不一致")
    for field in (
        "hostname",
        "os_name",
        "os_version",
        "architecture",
        "cpu_model",
        "cpu_physical_cores",
        "cpu_logical_cores",
        "memory_total_bytes",
        "agent_version",
    ):
        setattr(device, field, getattr(payload, field))
    device.last_seen_at = datetime.now(UTC)
    device.last_ip = request.client.host if request.client else None
    session.commit()
    return SystemInfoResponse(device_id=device.id, server_time=datetime.now(UTC))


@router.post("/metrics", response_model=MetricIngestResponse)
def metrics(
    payload: MetricRequest,
    session: DbSession,
    authorization: AuthorizationHeader = None,
) -> MetricIngestResponse:
    device = authenticated_device(session, authorization)
    accepted = ingest_metric(session, device, payload)
    session.commit()
    return MetricIngestResponse(
        accepted=int(accepted), duplicate=int(not accepted), server_time=datetime.now(UTC)
    )


@router.post("/metrics/batch", response_model=MetricIngestResponse)
def metrics_batch(
    payload: MetricBatchRequest,
    session: DbSession,
    authorization: AuthorizationHeader = None,
) -> MetricIngestResponse:
    device = authenticated_device(session, authorization)
    settings = get_settings()
    if len(payload.samples) > settings.max_agent_batch_samples:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"单批最多 {settings.max_agent_batch_samples} 条指标",
        )
    accepted = sum(ingest_metric(session, device, sample) for sample in payload.samples)
    session.commit()
    return MetricIngestResponse(
        accepted=accepted,
        duplicate=len(payload.samples) - accepted,
        server_time=datetime.now(UTC),
    )
