from types import SimpleNamespace

from sqlalchemy import func, select

from app import cli
from app.core.security import verify_password
from app.db.session import session_scope
from app.models.alert import AlertEvent
from app.models.device import Device
from app.models.metric import MetricSample
from app.models.user import User


def test_change_password_updates_hash(monkeypatch) -> None:
    answers = iter(["new-secure-password", "new-secure-password"])
    monkeypatch.setattr(cli, "getpass", lambda _: next(answers))

    assert cli.change_password("admin") == 0
    with session_scope() as session:
        user = session.scalar(select(User).where(User.username == "admin"))
        assert user is not None
        assert verify_password(user.password_hash, "new-secure-password")


def test_seed_demo_is_repeatable_and_preserves_real_devices() -> None:
    with session_scope() as session:
        session.add(Device(name="真实设备"))

    assert cli.seed_demo(confirm=True) == 0
    assert cli.seed_demo(confirm=True) == 0

    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(Device)) == 4
        assert session.scalar(select(func.count()).select_from(MetricSample)) == 214
        assert session.scalar(select(func.count()).select_from(AlertEvent)) == 3
        assert session.scalar(select(Device).where(Device.name == "真实设备")) is not None


def test_seed_demo_requires_confirmation() -> None:
    assert cli.seed_demo(confirm=False) == 1
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(Device)) == 0


def test_seed_demo_refuses_production(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: SimpleNamespace(app_env="production"))
    assert cli.seed_demo(confirm=True) == 1
