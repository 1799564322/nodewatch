import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255))
    agent_instance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), unique=True)
    os_name: Mapped[str | None] = mapped_column(String(64))
    os_version: Mapped[str | None] = mapped_column(String(255))
    architecture: Mapped[str | None] = mapped_column(String(64))
    cpu_model: Mapped[str | None] = mapped_column(String(255))
    cpu_physical_cores: Mapped[int | None] = mapped_column(Integer)
    cpu_logical_cores: Mapped[int | None] = mapped_column(Integer)
    memory_total_bytes: Mapped[int | None] = mapped_column(BigInteger)
    agent_version: Mapped[str | None] = mapped_column(String(32))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_ip: Mapped[str | None] = mapped_column(String(64))
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    maintenance_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tokens: Mapped[list["AgentToken"]] = relationship(  # noqa: F821
        back_populates="device", cascade="all, delete-orphan"
    )
