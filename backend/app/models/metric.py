import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MetricSample(Base):
    __tablename__ = "metric_samples"
    __table_args__ = (UniqueConstraint("device_id", "collected_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cpu_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    memory_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    memory_used_bytes: Mapped[int] = mapped_column(BigInteger)
    swap_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    root_disk_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    root_disk_used_bytes: Mapped[int | None] = mapped_column(BigInteger)
    net_tx_bytes_per_sec: Mapped[int] = mapped_column(BigInteger)
    net_rx_bytes_per_sec: Mapped[int] = mapped_column(BigInteger)
    uptime_seconds: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeviceLatestMetric(Base):
    __tablename__ = "device_latest_metrics"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cpu_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    memory_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    memory_used_bytes: Mapped[int] = mapped_column(BigInteger)
    swap_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    root_disk_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    root_disk_used_bytes: Mapped[int | None] = mapped_column(BigInteger)
    net_tx_bytes_per_sec: Mapped[int] = mapped_column(BigInteger)
    net_rx_bytes_per_sec: Mapped[int] = mapped_column(BigInteger)
    uptime_seconds: Mapped[int] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DiskLatestMetric(Base):
    __tablename__ = "disk_latest_metrics"
    __table_args__ = (UniqueConstraint("device_id", "mountpoint"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    mountpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    filesystem: Mapped[str | None] = mapped_column(String(64))
    total_bytes: Mapped[int] = mapped_column(BigInteger)
    used_bytes: Mapped[int] = mapped_column(BigInteger)
    percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
