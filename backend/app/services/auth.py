from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import generate_session_token, hash_session_token, verify_password
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.user_session import UserSession
from app.repositories.users import get_user_by_username


def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(session, username)
    if user is None or not user.is_active or not verify_password(user.password_hash, password):
        return None
    return user


def create_user_session(
    session: Session, user: User, ip_address: str | None, user_agent: str | None
) -> str:
    now = datetime.now(UTC)
    raw_token = generate_session_token()
    session.add(
        UserSession(
            user_id=user.id,
            session_hash=hash_session_token(raw_token),
            expires_at=now + timedelta(seconds=get_settings().session_ttl_seconds),
            last_seen_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )
    user.last_login_at = now
    return raw_token


def get_user_for_session(session: Session, raw_token: str) -> User | None:
    now = datetime.now(UTC)
    user_session = session.scalar(
        select(UserSession).where(
            UserSession.session_hash == hash_session_token(raw_token),
            UserSession.expires_at > now,
        )
    )
    if user_session is None or not user_session.user.is_active:
        return None
    user_session.last_seen_at = now
    return user_session.user


def delete_user_session(session: Session, raw_token: str) -> None:
    session.execute(
        delete(UserSession).where(UserSession.session_hash == hash_session_token(raw_token))
    )


def write_login_audit(
    session: Session, *, user: User | None, success: bool, ip_address: str | None
) -> None:
    session.add(
        AuditLog(
            user_id=user.id if user else None,
            action="auth.login.success" if success else "auth.login.failure",
            details={"success": success},
            ip_address=ip_address,
        )
    )

