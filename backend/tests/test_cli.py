from sqlalchemy import select

from app import cli
from app.core.security import verify_password
from app.db.session import session_scope
from app.models.user import User


def test_change_password_updates_hash(monkeypatch) -> None:
    answers = iter(["new-secure-password", "new-secure-password"])
    monkeypatch.setattr(cli, "getpass", lambda _: next(answers))

    assert cli.change_password("admin") == 0
    with session_scope() as session:
        user = session.scalar(select(User).where(User.username == "admin"))
        assert user is not None
        assert verify_password(user.password_hash, "new-secure-password")
