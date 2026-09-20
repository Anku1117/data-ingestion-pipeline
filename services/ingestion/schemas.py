from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from pydantic import BaseModel, Field

from libraries.schemas.common import Severity


class EventCreateRequest(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=255, description="Type of the event")
    source: str = Field(..., min_length=1, max_length=255, description="Source system")
    producer: str = Field(
        ..., min_length=1, max_length=255, description="Producer within the source"
    )
    payload: dict[str, Any] = Field(default_factory=dict, description="Event payload")
    severity: Severity = Field(default=Severity.INFO)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str | None = None
    trace_id: str | None = None
    timestamp: datetime | None = None


class EventCreateResponse(BaseModel):
    event_id: str
    status: str = "accepted"
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    environment: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None
