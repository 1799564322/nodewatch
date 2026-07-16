import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent_token import AgentToken
from app.models.audit_log import AuditLog
from app.models.device import Device


def get_device_or_404(session: Session, device_id: uuid.UUID) -> Device:
    device = session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    return device


def list_devices(session: Session, page: int, page_size: int) -> tuple[list[Device], int]:
    total = session.scalar(select(func.count()).select_from(Device)) or 0
    items = list(
        session.scalars(
            select(Device)
            .order_by(Device.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return items, total


def create_agent_token(session: Session, device: Device, user_id: uuid.UUID) -> tuple[AgentToken, str]:
    now = datetime.now(UTC)
    for token in session.scalars(
        select(AgentToken).where(
            AgentToken.device_id == device.id, AgentToken.revoked_at.is_(None)
        )
    ):
        token.revoked_at = now
    raw_token = f"nwa_{secrets.token_urlsafe(32)}"
    token = AgentToken(
        device_id=device.id,
        token_prefix=raw_token[:12],
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
    )
    session.add(token)
    session.flush()
    session.add(
        AuditLog(
            user_id=user_id,
            action="agent_token.generate",
            resource_type="device",
            resource_id=str(device.id),
            details={"token_id": str(token.id), "token_prefix": token.token_prefix},
        )
    )
    return token, raw_token


def authenticate_agent_token(session: Session, raw_token: str) -> tuple[AgentToken, Device]:
    candidate = hashlib.sha256(raw_token.encode()).hexdigest()
    token = session.scalar(select(AgentToken).where(AgentToken.token_hash == candidate))
    if token is None or not hmac.compare_digest(token.token_hash, candidate):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Agent Token 无效")
    now = datetime.now(UTC)
    if token.revoked_at is not None or (token.expires_at and token.expires_at <= now):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent Token 已失效")
    device = token.device
    if not device.is_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="设备已禁用")
    token.last_used_at = now
    return token, device
