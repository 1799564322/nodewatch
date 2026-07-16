from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import session_scope
from app.models.alert import AlertEvent, AlertRule
from app.models.device import Device
from app.models.metric import MetricSample
from app.models.user import User
from app.models.user_session import UserSession
from app.services.alerts import evaluate_metric_alerts, evaluate_offline_devices
from app.services.scheduler import cleanup_expired_data


def sample(device_id, when, cpu) -> MetricSample:
    return MetricSample(
        device_id=device_id,
        collected_at=when,
        received_at=when,
        cpu_percent=cpu,
        memory_percent=50,
        memory_used_bytes=1,
        net_tx_bytes_per_sec=0,
        net_rx_bytes_per_sec=0,
        uptime_seconds=1,
    )


def test_firing_acknowledged_resolved_and_no_duplicate(client: TestClient) -> None:
    now = datetime.now(UTC)
    with session_scope() as session:
        device = Device(name="alert-device", last_seen_at=now)
        rule = AlertRule(
            name="测试 CPU", metric="cpu", operator="gt", threshold=Decimal("10"),
            duration_seconds=120, severity="warning", cooldown_seconds=600, is_enabled=True,
        )
        session.add_all([device, rule])
        session.flush()
        first = sample(device.id, now - timedelta(seconds=60), Decimal("20"))
        second = sample(device.id, now, Decimal("30"))
        session.add_all([first, second])
        session.flush()
        evaluate_metric_alerts(session, device, second)
        evaluate_metric_alerts(session, device, second)

    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(AlertEvent)) == 1
        event_id = session.scalar(select(AlertEvent.id))
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "correct-horse-battery-staple"})
    assert login.status_code == 200
    acknowledged = client.post(f"/api/v1/alerts/{event_id}/acknowledge")
    assert acknowledged.json()["status"] == "acknowledged"

    with session_scope() as session:
        device = session.scalar(select(Device).where(Device.name == "alert-device"))
        recovered = sample(device.id, now + timedelta(seconds=60), Decimal("5"))
        session.add(recovered)
        session.flush()
        evaluate_metric_alerts(session, device, recovered)
    assert client.get("/api/v1/alerts").json()[0]["status"] == "resolved"


def test_offline_excludes_maintenance_and_recovers() -> None:
    now = datetime.now(UTC)
    with session_scope() as session:
        rule = AlertRule(name="离线测试", metric="offline", operator="gt", threshold=None, duration_seconds=180, severity="critical", cooldown_seconds=600, is_enabled=True)
        offline = Device(name="offline", last_seen_at=now - timedelta(seconds=181))
        maintained = Device(name="maintained", last_seen_at=now - timedelta(seconds=181), maintenance_until=now + timedelta(hours=1))
        session.add_all([rule, offline, maintained])
        session.flush()
        evaluate_offline_devices(session)
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(AlertEvent)) == 1
        device = session.scalar(select(Device).where(Device.name == "offline"))
        device.last_seen_at = datetime.now(UTC)
        evaluate_offline_devices(session)
    with session_scope() as session:
        assert session.scalar(select(AlertEvent.status)) == "resolved"


def test_cleanup_removes_expired_sessions_and_old_metrics() -> None:
    now = datetime.now(UTC)
    with session_scope() as session:
        user = session.scalar(select(User).where(User.username == "admin"))
        device = Device(name="cleanup-device")
        session.add(device)
        session.flush()
        session.add(sample(device.id, now - timedelta(days=31), Decimal("1")))
        session.add(UserSession(user_id=user.id, session_hash="a" * 64, expires_at=now - timedelta(days=1), last_seen_at=now - timedelta(days=2)))
    cleanup_expired_data()
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(MetricSample)) == 0
        assert session.scalar(select(func.count()).select_from(UserSession)) == 0
