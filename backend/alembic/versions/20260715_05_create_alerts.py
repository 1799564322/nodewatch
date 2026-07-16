"""创建告警规则和事件表

Revision ID: 20260715_05
Revises: 20260715_04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260715_05"
down_revision = "20260715_04"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True)),
        sa.Column("metric", sa.String(32), nullable=False),
        sa.Column("operator", sa.String(8), nullable=False),
        sa.Column("threshold", sa.Numeric(10, 2)),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("cooldown_seconds", sa.Integer(), server_default="600", nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"),
    )
    op.create_table(
        "alert_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("observed_value", sa.Numeric(10, 2)),
        sa.Column("threshold_value", sa.Numeric(10, 2)),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["alert_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_events_device_id", "alert_events", ["device_id"])
    op.create_index("ix_alert_events_rule_id", "alert_events", ["rule_id"])
    op.create_index("uq_alert_events_active", "alert_events", ["device_id", "rule_id"], unique=True, postgresql_where=sa.text("resolved_at IS NULL"))

def downgrade() -> None:
    op.drop_index("uq_alert_events_active", table_name="alert_events")
    op.drop_index("ix_alert_events_rule_id", table_name="alert_events")
    op.drop_index("ix_alert_events_device_id", table_name="alert_events")
    op.drop_table("alert_events")
    op.drop_table("alert_rules")
