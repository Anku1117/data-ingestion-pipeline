"""create alerts table for threat detection persistence

Revision ID: 003
Revises: 002
Create Date: 2026-09-21
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.String(64), primary_key=True),
        sa.Column("threat_type", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("event_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_alerts_threat_severity", "alerts", ["threat_type", "severity"])
    op.create_index("idx_alerts_timestamp", "alerts", ["timestamp"])


def downgrade() -> None:
    op.drop_index("idx_alerts_timestamp", table_name="alerts")
    op.drop_index("idx_alerts_threat_severity", table_name="alerts")
    op.drop_table("alerts")
