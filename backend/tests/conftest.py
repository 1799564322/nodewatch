import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://nodewatch:nodewatch@localhost:5432/nodewatch_test"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-longer-than-thirty-two-bytes")
os.environ.setdefault("BOOTSTRAP_ADMIN_USERNAME", "admin")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "correct-horse-battery-staple")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")
os.environ.setdefault("ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
os.environ.setdefault("RUN_SCHEDULER", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.security import hash_password
from app.db.session import session_scope
from app.main import app
from app.models.audit_log import AuditLog
from app.models.agent_token import AgentToken
from app.models.alert import AlertEvent, AlertRule
from app.models.device import Device
from app.models.metric import DeviceLatestMetric, DiskLatestMetric, MetricSample
from app.models.user import User
from app.models.user_session import UserSession


@pytest.fixture(autouse=True)
def reset_database():
    with session_scope() as session:
        session.execute(delete(AuditLog))
        session.execute(delete(AlertEvent))
        session.execute(delete(AlertRule))
        session.execute(delete(AgentToken))
        session.execute(delete(DeviceLatestMetric))
        session.execute(delete(DiskLatestMetric))
        session.execute(delete(MetricSample))
        session.execute(delete(Device))
        session.execute(delete(UserSession))
        session.execute(delete(User))
        session.add(
            User(
                username="admin",
                password_hash=hash_password("correct-horse-battery-staple"),
                role="admin",
                is_active=True,
            )
        )
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
