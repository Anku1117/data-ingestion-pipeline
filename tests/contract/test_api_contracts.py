from __future__ import annotations

import pytest
from pydantic import ValidationError

from services.agent_data.models import AgentRun, AgentStep, RunStatus, StepType
from services.detector.models import ThreatAlert, ThreatSeverity, ThreatType
from services.ingestion.schemas import (
    ErrorResponse,
    EventCreateRequest,
    EventCreateResponse,
    HealthResponse,
)
from services.processor.base import ProcessingResult, ValidationResult


class TestEventCreateRequestContract:
    def test_minimal(self) -> None:
        req = EventCreateRequest(event_type="T", source="s", producer="p")
        assert req.event_type == "T"
        assert req.source == "s"
        assert req.producer == "p"

    def test_event_type_min_length(self) -> None:
        with pytest.raises(ValidationError):
            EventCreateRequest(event_type="", source="s", producer="p")

    def test_event_type_max_length(self) -> None:
        with pytest.raises(ValidationError):
            EventCreateRequest(event_type="x" * 300, source="s", producer="p")

    def test_source_required(self) -> None:
        with pytest.raises(ValidationError):
            EventCreateRequest(event_type="T", producer="p")

    def test_optional_fields(self) -> None:
        req = EventCreateRequest(
            event_type="T", source="s", producer="p",
            tenant_id="t1", trace_id="tr1",
        )
        assert req.tenant_id == "t1"
        assert req.trace_id == "tr1"


class TestEventCreateResponseContract:
    def test_response(self) -> None:
        from datetime import UTC, datetime
        resp = EventCreateResponse(
            event_id="evt_123", status="accepted", timestamp=datetime.now(UTC),
        )
        assert resp.event_id == "evt_123"
        assert resp.status == "accepted"


class TestHealthResponseContract:
    def test_health(self) -> None:
        resp = HealthResponse(status="healthy", version="0.1.0", environment="test")
        assert resp.status == "healthy"
        assert resp.version == "0.1.0"


class TestErrorResponseContract:
    def test_error(self) -> None:
        err = ErrorResponse(error="test_error", detail="Something")
        assert err.error == "test_error"
        assert err.request_id is None


class TestThreatAlertContract:
    def test_alert(self) -> None:
        alert = ThreatAlert(
            threat_type=ThreatType.BRUTE_FORCE,
            severity=ThreatSeverity.HIGH,
            confidence=0.85,
            source="auth",
            description="Brute force detected",
        )
        assert alert.alert_id.startswith("alert_")
        assert alert.threat_type == ThreatType.BRUTE_FORCE
        assert alert.confidence == 0.85


class TestAgentRunContract:
    def test_run(self) -> None:
        run = AgentRun(task_id="t1", agent_id="a1")
        assert run.run_id.startswith("run_")
        assert run.status == RunStatus.PENDING


class TestAgentStepContract:
    def test_step(self) -> None:
        step = AgentStep(run_id="r1", step_number=1, step_type=StepType.MODEL_CALL)
        assert step.step_id.startswith("step_")
        assert step.step_type == StepType.MODEL_CALL


class TestProcessingResultContract:
    def test_valid_result(self) -> None:
        from libraries.schemas.common import EventEnvelope
        event = EventEnvelope(event_type="T", source="s", producer="p")
        result = ProcessingResult(status=ValidationResult.VALID, event=event)
        assert result.is_valid is True
        assert result.should_dlq is False

    def test_dlq_result(self) -> None:
        from libraries.schemas.common import EventEnvelope
        event = EventEnvelope(event_type="T", source="s", producer="p")
        result = ProcessingResult(status=ValidationResult.PERMANENT_FAILURE, event=event)
        assert result.should_dlq is True
