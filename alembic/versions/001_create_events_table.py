"""create events table

Revision ID: 001
Revises:
Create Date: 2026-09-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("event_id", sa.String(64), primary_key=True),
        sa.Column("event_version", sa.String(16), nullable=False, server_default="1.0"),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("producer", sa.String(255), nullable=False),
        sa.Column("tenant_id", sa.String(64), nullable=True),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=True),
        sa.Column("task_id", sa.String(64), nullable=True),
        sa.Column("agent_id", sa.String(64), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("severity", sa.String(16), nullable=False, server_default="info"),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("schema_version", sa.String(16), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index("idx_events_event_type", "events", ["event_type"])
    op.create_index("idx_events_source", "events", ["source"])
    op.create_index("idx_events_timestamp", "events", ["timestamp"])
    op.create_index("idx_events_trace_id", "events", ["trace_id"])
    op.create_index(
        "idx_events_tenant_id",
        "events",
        ["tenant_id"],
        postgresql_where="tenant_id IS NOT NULL",
    )
    op.create_index(
        "idx_events_agent_id",
        "events",
        ["agent_id"],
        postgresql_where="agent_id IS NOT NULL",
    )
    op.create_index("idx_events_severity", "events", ["severity"])
    op.create_index(
        "idx_events_run_id",
        "events",
        ["run_id"],
        postgresql_where="run_id IS NOT NULL",
    )
    op.create_index(
        "idx_events_severity_agent",
        "events",
        ["severity", "agent_id"],
        postgresql_where="agent_id IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_table("events")
