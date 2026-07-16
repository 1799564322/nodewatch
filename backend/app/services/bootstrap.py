import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User
from app.repositories.users import count_users

logger = logging.getLogger(__name__)


def bootstrap_admin(session: Session) -> User | None:
    settings = get_settings()
    if count_users(session) > 0:
        return None
    if not settings.bootstrap_admin_username or not settings.bootstrap_admin_password:
        logger.info("用户表为空，但未配置 bootstrap 管理员")
        return None

    user = User(
        username=settings.bootstrap_admin_username.strip().lower(),
        password_hash=hash_password(settings.bootstrap_admin_password),
        role="admin",
        is_active=True,
    )
    session.add(user)
    session.flush()
    logger.info("已创建 bootstrap 管理员", extra={"user_id": str(user.id)})
    return user

