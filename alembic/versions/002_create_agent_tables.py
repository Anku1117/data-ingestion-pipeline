"""create agent data tables

Revision ID: 002
Revises: 001
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("run_id", sa.String(64), primary_key=True),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.Text, nullable=True),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_steps", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_agent_runs_task_id", "agent_runs", ["task_id"])
    op.create_index("idx_agent_runs_agent_id", "agent_runs", ["agent_id"])
    op.create_index("idx_agent_runs_status", "agent_runs", ["status"])
    op.create_index("idx_agent_runs_agent_status", "agent_runs", ["agent_id", "status"])

    op.create_table(
        "agent_steps",
        sa.Column("step_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("step_type", sa.String(32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("parent_event_id", sa.String(64), nullable=True),
        sa.Column("model_id", sa.String(128), nullable=True),
        sa.Column("model_name", sa.String(128), nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("tool_name", sa.String(128), nullable=True),
        sa.Column("tool_status", sa.String(32), nullable=True),
        sa.Column("tool_input", sa.JSON, nullable=True),
        sa.Column("tool_output", sa.JSON, nullable=True),
        sa.Column("retrieval_ids", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("idx_agent_steps_run_id", "agent_steps", ["run_id"])
    op.create_index("idx_agent_steps_run_sequence", "agent_steps", ["run_id", "step_number"])

    op.create_table(
        "agent_evaluations",
        sa.Column("evaluation_id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False, unique=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("success", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("score", sa.Float, nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tool_failures", sa.Integer, nullable=False, server_default="0"),
        sa.Column("task_completion", sa.Float, nullable=False, server_default="0"),
        sa.Column("anomaly_score", sa.Float, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_agent_evaluations_run_id", "agent_evaluations", ["run_id"], unique=True)
    op.create_index("idx_agent_evaluations_agent_id", "agent_evaluations", ["agent_id"])

    op.create_table(
        "agent_tasks",
        sa.Column("task_id", sa.String(64), primary_key=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_agent_tasks_agent_id", "agent_tasks", ["agent_id"])


def downgrade() -> None:
    op.drop_table("agent_tasks")
    op.drop_table("agent_evaluations")
    op.drop_table("agent_steps")
    op.drop_table("agent_runs")
