"""创建设备与 Agent Token 表

Revision ID: 20260715_02
Revises: 20260714_01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260715_02"
down_revision = "20260714_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("hostname", sa.String(255)),
        sa.Column("agent_instance_id", postgresql.UUID(as_uuid=True)),
        sa.Column("os_name", sa.String(64)),
        sa.Column("os_version", sa.String(255)),
        sa.Column("architecture", sa.String(64)),
        sa.Column("cpu_model", sa.String(255)),
        sa.Column("cpu_physical_cores", sa.Integer()),
        sa.Column("cpu_logical_cores", sa.Integer()),
        sa.Column("memory_total_bytes", sa.BigInteger()),
        sa.Column("agent_version", sa.String(32)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("last_ip", sa.String(64)),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("maintenance_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_instance_id"),
    )
    op.create_table(
        "agent_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_prefix", sa.String(16), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_agent_tokens_device_id", "agent_tokens", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_tokens_device_id", table_name="agent_tokens")
    op.drop_table("agent_tokens")
    op.drop_table("devices")
