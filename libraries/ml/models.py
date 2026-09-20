from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AnomalyResult(BaseModel):
    anomaly_id: str = Field(default_factory=lambda: f"anomaly_{uuid.uuid4().hex}")
    event_id: str | None = None
    run_id: str | None = None
    anomaly_score: float = Field(ge=0.0, le=1.0)
    is_anomaly: bool = False
    model_version: str = "1.0"
    feature_version: str = "1.0"
    detection_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    features: dict[str, float] = Field(default_factory=dict)
    explanation: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeatureVector(BaseModel):
    events_per_minute: float = 0.0
    failed_login_count: float = 0.0
    unique_users: float = 0.0
    unique_ports: float = 0.0
    request_frequency: float = 0.0
    event_frequency: float = 0.0
    avg_payload_size: float = 0.0
    unique_event_types: float = 0.0
    error_ratio: float = 0.0
    agent_step_count: float = 0.0
