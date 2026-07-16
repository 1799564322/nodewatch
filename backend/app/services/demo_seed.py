import math
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.alert import AlertEvent, AlertRule
from app.models.device import Device
from app.models.metric import DeviceLatestMetric, DiskLatestMetric, MetricSample
from app.services.alerts import bootstrap_alert_rules

DEMO_DEVICES = (
    (uuid.UUID("00000000-0000-4000-8000-000000000101"), "[演示] Web-01", "web-01", "Ubuntu"),
    (uuid.UUID("00000000-0000-4000-8000-000000000102"), "[演示] DB-01", "db-01", "Ubuntu"),
    (uuid.UUID("00000000-0000-4000-8000-000000000103"), "[演示] 离线节点", "edge-01", "Windows"),
)


def _percent(value: float) -> Decimal:
    return Decimal(f"{value:.2f}")


def seed_demo_data(session: Session, now: datetime | None = None) -> dict[str, int]:
    now = (now or datetime.now(UTC)).replace(second=0, microsecond=0)
    expected_names = {device_id: name for device_id, name, _, _ in DEMO_DEVICES}
    demo_ids = tuple(expected_names)
    existing = list(session.scalars(select(Device).where(Device.id.in_(demo_ids))))
    for device in existing:
        if device.name != expected_names[device.id]:
            raise RuntimeError(f"演示设备 ID 已被真实设备占用：{device.id}")

    session.execute(delete(Device).where(Device.id.in_(demo_ids)))
    session.flush()
    bootstrap_alert_rules(session)
    session.flush()

    latest_by_id: dict[uuid.UUID, MetricSample] = {}
    for index, (device_id, name, hostname, os_name) in enumerate(DEMO_DEVICES):
        is_offline = index == 2
        last_seen_at = now - timedelta(hours=2) if is_offline else now
        memory_total = 8 * 1024**3 if index != 1 else 16 * 1024**3
        device = Device(
            id=device_id,
            name=name,
            hostname=hostname,
            os_name=os_name,
            os_version="24.04 LTS" if os_name == "Ubuntu" else "11",
            architecture="x86_64",
            cpu_model="Demo CPU",
            cpu_physical_cores=4,
            cpu_logical_cores=8,
            memory_total_bytes=memory_total,
            agent_version="1.0.0",
            last_seen_at=last_seen_at,
            last_ip="192.0.2.10",
            is_enabled=True,
        )
        session.add(device)

        points = 70 if is_offline else 72
        for point in range(points):
            collected_at = now - timedelta(minutes=5 * (71 - point))
            cpu = 28 + index * 8 + math.sin(point / 5) * 12
            memory = 42 + index * 9 + math.cos(point / 7) * 6
            root_disk = (88 if index == 1 else 58 + index * 8) + math.sin(point / 11) * 2
            sample = MetricSample(
                device_id=device_id,
                collected_at=collected_at,
                received_at=collected_at + timedelta(seconds=1),
                cpu_percent=_percent(cpu),
                memory_percent=_percent(memory),
                memory_used_bytes=int(memory_total * memory / 100),
                swap_percent=_percent(0 if index == 0 else 4 + index),
                root_disk_percent=_percent(root_disk),
                root_disk_used_bytes=int(200 * 1024**3 * root_disk / 100),
                net_tx_bytes_per_sec=12000 + point * 80 + index * 2000,
                net_rx_bytes_per_sec=28000 + point * 120 + index * 3000,
                uptime_seconds=86400 * (12 + index) + point * 300,
            )
            session.add(sample)
            latest_by_id[device_id] = sample

        latest = latest_by_id[device_id]
        session.add(
            DeviceLatestMetric(
                device_id=device_id,
                collected_at=latest.collected_at,
                received_at=latest.received_at,
                cpu_percent=latest.cpu_percent,
                memory_percent=latest.memory_percent,
                memory_used_bytes=latest.memory_used_bytes,
                swap_percent=latest.swap_percent,
                root_disk_percent=latest.root_disk_percent,
                root_disk_used_bytes=latest.root_disk_used_bytes,
                net_tx_bytes_per_sec=latest.net_tx_bytes_per_sec,
                net_rx_bytes_per_sec=latest.net_rx_bytes_per_sec,
                uptime_seconds=latest.uptime_seconds,
            )
        )
        session.add(
            DiskLatestMetric(
                device_id=device_id,
                mountpoint="C:\\" if os_name == "Windows" else "/",
                filesystem="NTFS" if os_name == "Windows" else "ext4",
                total_bytes=200 * 1024**3,
                used_bytes=latest.root_disk_used_bytes or 0,
                percent=latest.root_disk_percent or Decimal(0),
                collected_at=latest.collected_at,
            )
        )

    root_rule = session.scalar(select(AlertRule).where(AlertRule.metric == "root_disk"))
    offline_rule = session.scalar(select(AlertRule).where(AlertRule.metric == "offline"))
    cpu_rule = session.scalar(select(AlertRule).where(AlertRule.metric == "cpu"))
    if root_rule and offline_rule and cpu_rule:
        session.add_all(
            [
                AlertEvent(
                    device_id=DEMO_DEVICES[1][0],
                    rule_id=root_rule.id,
                    status="firing",
                    severity=root_rule.severity,
                    title=root_rule.name,
                    message="[演示] DB-01 的系统盘持续超过阈值",
                    observed_value=Decimal("90.00"),
                    threshold_value=root_rule.threshold,
                    started_at=now - timedelta(minutes=18),
                    last_evaluated_at=now,
                ),
                AlertEvent(
                    device_id=DEMO_DEVICES[2][0],
                    rule_id=offline_rule.id,
                    status="firing",
                    severity=offline_rule.severity,
                    title=offline_rule.name,
                    message="[演示] 离线节点已超过 180 秒未上报",
                    started_at=now - timedelta(minutes=7),
                    last_evaluated_at=now,
                ),
                AlertEvent(
                    device_id=DEMO_DEVICES[0][0],
                    rule_id=cpu_rule.id,
                    status="resolved",
                    severity=cpu_rule.severity,
                    title=cpu_rule.name,
                    message="[演示] Web-01 的 CPU 告警已恢复",
                    observed_value=Decimal("93.00"),
                    threshold_value=cpu_rule.threshold,
                    started_at=now - timedelta(hours=2),
                    last_evaluated_at=now - timedelta(hours=1, minutes=45),
                    resolved_at=now - timedelta(hours=1, minutes=45),
                ),
            ]
        )

    return {"devices": len(DEMO_DEVICES), "metrics": sum(70 if index == 2 else 72 for index in range(3)), "alerts": 3}
