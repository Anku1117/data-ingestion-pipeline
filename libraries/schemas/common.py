from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def generate_event_id() -> str:
    return f"evt_{uuid.uuid4().hex}"


def generate_trace_id() -> str:
    return f"trace_{uuid.uuid4().hex}"


def generate_run_id() -> str:
    return f"run_{uuid.uuid4().hex}"


def generate_step_id() -> str:
    return f"step_{uuid.uuid4().hex}"


def utcnow() -> datetime:
    return datetime.now(UTC)


class Severity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=generate_event_id, description="Unique event identifier")
    event_version: str = Field(default="1.0", description="Schema version of this event")
    event_type: str = Field(..., description="Type of the event")
    timestamp: datetime = Field(
        default_factory=utcnow, description="UTC timestamp of event creation"
    )
    source: str = Field(..., description="Source system or component")
    producer: str = Field(..., description="Specific producer within the source")
    tenant_id: str | None = Field(
        default=None, description="Tenant identifier for multi-tenant isolation"
    )
    trace_id: str = Field(
        default_factory=generate_trace_id, description="Distributed trace identifier"
    )
    run_id: str | None = Field(default=None, description="Agent run identifier")
    task_id: str | None = Field(default=None, description="Task identifier")
    agent_id: str | None = Field(default=None, description="Agent identifier")
    session_id: str | None = Field(default=None, description="Session identifier")
    severity: Severity = Field(default=Severity.INFO, description="Event severity level")
    payload: dict[str, Any] = Field(default_factory=dict, description="Event-specific payload data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    schema_version: str = Field(default="1.0", description="Version of the event schema")
