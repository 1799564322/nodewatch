from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.metric import DeviceLatestMetric, DiskLatestMetric, MetricSample
from app.schemas.metric import MetricRequest
from app.services.alerts import evaluate_metric_alerts


def ingest_metric(session: Session, device: Device, payload: MetricRequest) -> bool:
    now = datetime.now(UTC)
    values = payload.model_dump(exclude={"sample_id", "disks"}) | {
        "device_id": device.id,
        "received_at": now,
    }
    inserted_id = session.scalar(
        insert(MetricSample)
        .values(**values)
        .on_conflict_do_nothing(index_elements=["device_id", "collected_at"])
        .returning(MetricSample.id)
    )
    accepted = inserted_id is not None
    if accepted:
        update_values = values | {"updated_at": now}
        session.execute(
            insert(DeviceLatestMetric)
            .values(**update_values)
            .on_conflict_do_update(
                index_elements=["device_id"],
                set_={key: value for key, value in update_values.items() if key != "device_id"},
                where=DeviceLatestMetric.collected_at < payload.collected_at,
            )
        )
        for disk in payload.disks:
            disk_values = disk.model_dump() | {
                "device_id": device.id,
                "collected_at": payload.collected_at,
                "updated_at": now,
            }
            session.execute(
                insert(DiskLatestMetric)
                .values(**disk_values)
                .on_conflict_do_update(
                    index_elements=["device_id", "mountpoint"],
                    set_={key: value for key, value in disk_values.items() if key != "device_id"},
                    where=DiskLatestMetric.collected_at < payload.collected_at,
                )
            )
    device.last_seen_at = now
    if accepted:
        sample = session.scalar(
            select(MetricSample).where(
                MetricSample.device_id == device.id,
                MetricSample.collected_at == payload.collected_at,
            )
        )
        if sample:
            evaluate_metric_alerts(session, device, sample)
    return accepted
