from fastapi.testclient import TestClient


def test_live_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "nodewatch"}
    assert response.headers["X-Request-ID"].startswith("req_")


def test_ready_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ok",
        "migration": "20260715_05",
    }


def test_untrusted_host_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"host": "attacker.example"})
    assert response.status_code == 400
