import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import session_scope
from app.models.agent_token import AgentToken
from app.models.device import Device


def login(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 200


def create_device_and_token(client: TestClient) -> tuple[str, dict]:
    login(client)
    device = client.post("/api/v1/devices", json={"name": "测试电脑"})
    assert device.status_code == 201
    token = client.post(f"/api/v1/devices/{device.json()['id']}/tokens")
    assert token.status_code == 201
    return device.json()["id"], token.json()


def test_device_crud_and_token_is_only_stored_as_hash(client: TestClient) -> None:
    device_id, token_payload = create_device_and_token(client)
    raw_token = token_payload["token"]
    assert raw_token.startswith("nwa_")
    assert len(raw_token) >= 47

    listing = client.get("/api/v1/devices")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    with session_scope() as session:
        stored = session.scalar(select(AgentToken))
        assert stored is not None
        assert stored.token_hash != raw_token
        assert raw_token not in str(stored.__dict__)

    updated = client.patch(f"/api/v1/devices/{device_id}", json={"name": "新名称"})
    assert updated.json()["name"] == "新名称"


def test_agent_binding_system_info_revoke_and_disabled_device(client: TestClient) -> None:
    device_id, token_payload = create_device_and_token(client)
    headers = {"Authorization": f"Bearer {token_payload['token']}"}
    instance_id = str(uuid.uuid4())
    bootstrap = client.post(
        "/api/v1/agent/bootstrap",
        headers=headers,
        json={
            "agent_instance_id": instance_id,
            "agent_version": "0.1.0",
            "hostname": "learning-pc",
        },
    )
    assert bootstrap.status_code == 200
    assert bootstrap.json()["device_id"] == device_id

    stolen = client.post(
        "/api/v1/agent/bootstrap",
        headers=headers,
        json={
            "agent_instance_id": str(uuid.uuid4()),
            "agent_version": "0.1.0",
            "hostname": "other-pc",
        },
    )
    assert stolen.status_code == 409

    info = client.post(
        "/api/v1/agent/system-info",
        headers=headers,
        json={
            "agent_instance_id": instance_id,
            "hostname": "learning-pc",
            "os_name": "Windows",
            "os_version": "11",
            "architecture": "AMD64",
            "cpu_model": "Test CPU",
            "cpu_physical_cores": 4,
            "cpu_logical_cores": 8,
            "memory_total_bytes": 16_000_000_000,
            "agent_version": "0.1.0",
        },
    )
    assert info.status_code == 200
    with session_scope() as session:
        assert session.get(Device, uuid.UUID(device_id)).last_seen_at is not None

    revoked = client.post(
        f"/api/v1/devices/{device_id}/tokens/{token_payload['token_id']}/revoke"
    )
    assert revoked.status_code == 204
    assert client.post("/api/v1/agent/bootstrap", headers=headers, json={
        "agent_instance_id": instance_id,
        "agent_version": "0.1.0",
        "hostname": "learning-pc",
    }).status_code == 403


def test_disabled_device_rejects_agent(client: TestClient) -> None:
    device_id, token_payload = create_device_and_token(client)
    client.delete(f"/api/v1/devices/{device_id}")
    response = client.post(
        "/api/v1/agent/bootstrap",
        headers={"Authorization": f"Bearer {token_payload['token']}"},
        json={
            "agent_instance_id": str(uuid.uuid4()),
            "agent_version": "0.1.0",
            "hostname": "disabled-pc",
        },
    )
    assert response.status_code == 403
