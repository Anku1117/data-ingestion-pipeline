from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ThreatType(str, Enum):
    BRUTE_FORCE = "brute_force"
    PORT_SCAN = "port_scan"
    HIGH_REQUEST_FREQUENCY = "high_request_frequency"
    AUTH_ANOMALY = "auth_anomaly"
    UNUSUAL_ACCESS = "unusual_access"
    SUSPICIOUS_PAYLOAD = "suspicious_payload"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"


class ThreatSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: f"alert_{uuid.uuid4().hex}")
    threat_type: ThreatType
    severity: ThreatSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str
    description: str
    event_ids: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    acknowledged: bool = False


class DetectionResult(BaseModel):
    detected: bool
    alerts: list[ThreatAlert] = Field(default_factory=list)
    features: dict[str, Any] = Field(default_factory=dict)
    rule_name: str
    evaluation_time_ms: float = 0.0
