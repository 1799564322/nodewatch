import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import session_scope
from app.models.metric import DeviceLatestMetric, DiskLatestMetric, MetricSample
from app.models.device import Device
from tests.test_devices import create_device_and_token


def payload(collected_at: datetime, cpu: float) -> dict:
    return {
        "sample_id": str(uuid.uuid4()),
        "collected_at": collected_at.isoformat(),
        "cpu_percent": cpu,
        "memory_percent": 55.2,
        "memory_used_bytes": 8_000_000_000,
        "swap_percent": 0,
        "root_disk_percent": 60.1,
        "root_disk_used_bytes": 120_000_000_000,
        "net_tx_bytes_per_sec": 1000,
        "net_rx_bytes_per_sec": 2000,
        "uptime_seconds": 3600,
        "disks": [
            {
                "mountpoint": "C:\\\\",
                "filesystem": "NTFS",
                "total_bytes": 200_000_000_000,
                "used_bytes": 120_000_000_000,
                "percent": 60,
            }
        ],
    }


def test_metric_is_idempotent_and_latest_rejects_older_sample(client: TestClient) -> None:
    _, token = create_device_and_token(client)
    headers = {"Authorization": f"Bearer {token['token']}"}
    now = datetime.now(UTC).replace(microsecond=0)

    first = client.post("/api/v1/agent/metrics", headers=headers, json=payload(now, 20))
    duplicate = client.post("/api/v1/agent/metrics", headers=headers, json=payload(now, 99))
    newer = client.post(
        "/api/v1/agent/metrics", headers=headers, json=payload(now + timedelta(minutes=1), 40)
    )
    older = client.post(
        "/api/v1/agent/metrics", headers=headers, json=payload(now - timedelta(minutes=1), 90)
    )

    assert first.json()["accepted"] == 1
    assert duplicate.json()["duplicate"] == 1
    assert newer.json()["accepted"] == 1
    assert older.json()["accepted"] == 1
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(MetricSample)) == 3
        latest = session.scalar(select(DeviceLatestMetric))
        assert latest is not None
        assert float(latest.cpu_percent) == 40
        disk = session.scalar(select(DiskLatestMetric))
        assert disk is not None
        assert float(disk.percent) == 60


def test_dashboard_handles_fifty_devices(client: TestClient) -> None:
    with session_scope() as session:
        session.add_all([Device(name=f"scale-device-{index:02d}") for index in range(50)])
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "correct-horse-battery-staple"},
    )
    assert login.status_code == 200
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    assert response.json()["total_devices"] == 50
    assert response.json()["offline_devices"] == 50


def test_metric_batch_is_idempotent(client: TestClient) -> None:
    _, token = create_device_and_token(client)
    headers = {"Authorization": f"Bearer {token['token']}"}
    now = datetime.now(UTC).replace(microsecond=0)
    samples = [payload(now + timedelta(minutes=index), 20 + index) for index in range(3)]

    first = client.post("/api/v1/agent/metrics/batch", headers=headers, json={"samples": samples})
    duplicate = client.post(
        "/api/v1/agent/metrics/batch", headers=headers, json={"samples": samples}
    )

    assert first.status_code == 200
    assert first.json()["accepted"] == 3
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] == 3


def test_history_range_resolution_and_disks(client: TestClient) -> None:
    device_id, token = create_device_and_token(client)
    headers = {"Authorization": f"Bearer {token['token']}"}
    now = datetime.now(UTC).replace(microsecond=0)
    client.post("/api/v1/agent/metrics", headers=headers, json=payload(now, 25))

    raw = client.get(
        f"/api/v1/devices/{device_id}/metrics/history",
        params={"from": (now - timedelta(hours=1)).isoformat(), "to": now.isoformat()},
    )
    assert raw.status_code == 200
    assert raw.json()["resolution"] == "raw"
    assert len(raw.json()["points"]) == 1

    aggregated = client.get(
        f"/api/v1/devices/{device_id}/metrics/history",
        params={"from": (now - timedelta(days=7)).isoformat(), "to": now.isoformat()},
    )
    assert aggregated.status_code == 200
    assert aggregated.json()["resolution"] == "1h"
    disks = client.get(f"/api/v1/devices/{device_id}/disks")
    assert disks.status_code == 200
    assert disks.json()[0]["filesystem"] == "NTFS"

    too_wide = client.get(
        f"/api/v1/devices/{device_id}/metrics/history",
        params={"from": (now - timedelta(days=32)).isoformat(), "to": now.isoformat()},
    )
    assert too_wide.status_code == 422
