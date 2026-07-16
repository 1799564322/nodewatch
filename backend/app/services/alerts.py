import math
import operator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import AlertEvent, AlertRule
from app.models.device import Device
from app.models.metric import MetricSample

DEFAULT_RULES = [
    ("CPU 使用率过高", "cpu", "gt", 90, 300, "warning"),
    ("内存使用率过高", "memory", "gt", 90, 300, "warning"),
    ("系统盘使用率过高", "root_disk", "gt", 85, 120, "warning"),
    ("设备离线", "offline", "gt", None, 180, "critical"),
]
OPERATORS = {"gt": operator.gt, "gte": operator.ge, "lt": operator.lt, "lte": operator.le}
METRIC_COLUMNS = {
    "cpu": MetricSample.cpu_percent,
    "memory": MetricSample.memory_percent,
    "root_disk": MetricSample.root_disk_percent,
}


def bootstrap_alert_rules(session: Session) -> None:
    existing = set(session.scalars(select(AlertRule.name)))
    for name, metric, op, threshold, duration, severity in DEFAULT_RULES:
        if name not in existing:
            session.add(
                AlertRule(
                    name=name,
                    metric=metric,
                    operator=op,
                    threshold=threshold,
                    duration_seconds=duration,
                    severity=severity,
                    cooldown_seconds=600,
                    is_enabled=True,
                )
            )


def _active_event(session: Session, device_id, rule_id) -> AlertEvent | None:
    return session.scalar(
        select(AlertEvent).where(
            AlertEvent.device_id == device_id,
            AlertEvent.rule_id == rule_id,
            AlertEvent.resolved_at.is_(None),
        )
    )


def _resolve(event: AlertEvent, now: datetime) -> None:
    event.status = "resolved"
    event.resolved_at = now
    event.last_evaluated_at = now


def evaluate_metric_alerts(session: Session, device: Device, sample: MetricSample) -> None:
    now = datetime.now(UTC)
    if sample.received_at - sample.collected_at > timedelta(seconds=120):
        return
    rules = session.scalars(
        select(AlertRule).where(
            AlertRule.is_enabled.is_(True),
            AlertRule.metric.in_(METRIC_COLUMNS),
            (AlertRule.device_id.is_(None) | (AlertRule.device_id == device.id)),
        )
    )
    for rule in rules:
        column = METRIC_COLUMNS[rule.metric]
        current = getattr(sample, column.key)
        if current is None or rule.threshold is None:
            continue
        active = _active_event(session, device.id, rule.id)
        recovery_threshold = rule.threshold - 3 if rule.metric == "root_disk" else rule.threshold
        if active and current <= recovery_threshold:
            _resolve(active, now)
            continue
        required = max(1, math.ceil(rule.duration_seconds / 60))
        recent = list(
            session.scalars(
                select(MetricSample)
                .where(
                    MetricSample.device_id == device.id,
                    MetricSample.collected_at >= sample.collected_at - timedelta(seconds=rule.duration_seconds),
                    MetricSample.received_at - MetricSample.collected_at <= timedelta(seconds=120),
                )
                .order_by(MetricSample.collected_at.desc())
                .limit(required)
            )
        )
        values = [getattr(item, column.key) for item in recent]
        firing = len(values) >= required and all(
            value is not None and OPERATORS[rule.operator](value, rule.threshold) for value in values
        )
        if firing and active is None:
            session.add(
                AlertEvent(
                    device_id=device.id,
                    rule_id=rule.id,
                    status="firing",
                    severity=rule.severity,
                    title=rule.name,
                    message=f"{device.name} 的 {rule.metric} 持续超过阈值",
                    observed_value=Decimal(current),
                    threshold_value=rule.threshold,
                    started_at=now,
                    last_evaluated_at=now,
                )
            )
        elif active:
            active.last_evaluated_at = now


def evaluate_offline_devices(session: Session) -> None:
    now = datetime.now(UTC)
    rules = list(session.scalars(select(AlertRule).where(AlertRule.metric == "offline", AlertRule.is_enabled.is_(True))))
    devices = session.scalars(select(Device))
    for device in devices:
        for rule in rules:
            active = _active_event(session, device.id, rule.id)
            maintained = device.maintenance_until is not None and device.maintenance_until > now
            eligible = device.is_enabled and not maintained and device.last_seen_at is not None
            offline = eligible and now - device.last_seen_at > timedelta(seconds=rule.duration_seconds)
            if offline and active is None:
                session.add(AlertEvent(device_id=device.id, rule_id=rule.id, status="firing", severity=rule.severity, title=rule.name, message=f"{device.name} 已超过 {rule.duration_seconds} 秒未上报", started_at=now, last_evaluated_at=now))
            elif not offline and active:
                _resolve(active, now)
