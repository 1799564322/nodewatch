import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.deps import require_admin
from app.db.session import session_scope
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.user_session import UserSession


def test_login_success_sets_secure_session_shape(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "ADMIN", "password": "correct-horse-battery-staple"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["username"] == "admin"
    cookie = response.headers["set-cookie"]
    assert "nodewatch_session=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    with session_scope() as session:
        stored = session.scalar(select(UserSession))
        assert stored is not None
        assert stored.session_hash not in cookie
        assert len(stored.session_hash) == 64


def test_login_failure_is_generic_and_does_not_store_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"
    with session_scope() as session:
        audit = session.scalars(select(AuditLog)).one()
        assert audit.action == "auth.login.failure"
        assert "wrong-password" not in str(audit.details)


def test_session_survives_request_and_logout_invalidates_it(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "correct-horse-battery-staple"},
    )
    assert login.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    with session_scope() as session:
        assert session.scalar(select(UserSession)) is None


def test_viewer_is_rejected_by_admin_dependency() -> None:
    viewer = User(username="viewer", password_hash="unused", role="viewer", is_active=True)

    with pytest.raises(HTTPException) as exc_info:
        require_admin(viewer)

    assert exc_info.value.status_code == 403

