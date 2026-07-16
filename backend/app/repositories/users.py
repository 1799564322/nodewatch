from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username))


def count_users(session: Session) -> int:
    return len(session.scalars(select(User.id)).all())

