"""创建多磁盘最新状态表

Revision ID: 20260715_04
Revises: 20260715_03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260715_04"
down_revision = "20260715_03"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "disk_latest_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mountpoint", sa.String(255), nullable=False),
        sa.Column("filesystem", sa.String(64)),
        sa.Column("total_bytes", sa.BigInteger(), nullable=False),
        sa.Column("used_bytes", sa.BigInteger(), nullable=False),
        sa.Column("percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id", "mountpoint"),
    )
    op.create_index("ix_disk_latest_metrics_device_id", "disk_latest_metrics", ["device_id"])

def downgrade() -> None:
    op.drop_index("ix_disk_latest_metrics_device_id", table_name="disk_latest_metrics")
    op.drop_table("disk_latest_metrics")
