from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from libraries.schemas.common import Severity
from services.ingestion.schemas import (
    ErrorResponse,
    EventCreateRequest,
    EventCreateResponse,
    HealthResponse,
)


class TestEventCreateRequest:
    def test_valid_request(self) -> None:
        req = EventCreateRequest(
            event_type="LOGIN_FAILED",
            source="auth_service",
            producer="auth_v1",
        )
        assert req.event_type == "LOGIN_FAILED"
        assert req.severity == Severity.INFO
        assert req.payload == {}

    def test_with_payload(self) -> None:
        req = EventCreateRequest(
            event_type="TOOL_CALL",
            source="agent",
            producer="agent_v1",
            payload={"tool": "search", "query": "test"},
            severity=Severity.INFO,
            metadata={"ip": "10.0.0.1"},
        )
        assert req.payload["tool"] == "search"

    def test_empty_event_type_fails(self) -> None:
        with pytest.raises(ValidationError):
            EventCreateRequest(
                event_type="",
                source="test",
                producer="test",
            )

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            EventCreateRequest(event_type="TEST")


class TestEventCreateResponse:
    def test_response(self) -> None:
        ts = datetime.now(UTC)
        resp = EventCreateResponse(
            event_id="evt_123",
            status="accepted",
            timestamp=ts,
        )
        assert resp.event_id == "evt_123"
        assert resp.status == "accepted"


class TestHealthResponse:
    def test_health(self) -> None:
        resp = HealthResponse(status="healthy", version="0.1.0", environment="test")
        assert resp.status == "healthy"


class TestErrorResponse:
    def test_error(self) -> None:
        err = ErrorResponse(error="test_error", detail="Something went wrong")
        assert err.error == "test_error"
        assert err.request_id is None
