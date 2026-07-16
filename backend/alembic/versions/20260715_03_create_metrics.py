"""创建指标历史与最新状态表

Revision ID: 20260715_03
Revises: 20260715_02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260715_03"
down_revision = "20260715_02"
branch_labels = None
depends_on = None


def _metric_columns() -> list[sa.Column]:
    return [
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cpu_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("memory_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("memory_used_bytes", sa.BigInteger(), nullable=False),
        sa.Column("swap_percent", sa.Numeric(5, 2)),
        sa.Column("root_disk_percent", sa.Numeric(5, 2)),
        sa.Column("root_disk_used_bytes", sa.BigInteger()),
        sa.Column("net_tx_bytes_per_sec", sa.BigInteger(), nullable=False),
        sa.Column("net_rx_bytes_per_sec", sa.BigInteger(), nullable=False),
        sa.Column("uptime_seconds", sa.BigInteger(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "metric_samples",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        *_metric_columns(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id", "collected_at"),
    )
    op.create_index("ix_metric_samples_device_id", "metric_samples", ["device_id"])
    op.create_index("ix_metric_samples_collected_at", "metric_samples", ["collected_at"])
    op.create_table(
        "device_latest_metrics",
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        *_metric_columns(),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("device_id"),
    )


def downgrade() -> None:
    op.drop_table("device_latest_metrics")
    op.drop_index("ix_metric_samples_collected_at", table_name="metric_samples")
    op.drop_index("ix_metric_samples_device_id", table_name="metric_samples")
    op.drop_table("metric_samples")
