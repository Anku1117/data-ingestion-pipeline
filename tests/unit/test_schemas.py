from __future__ import annotations

from datetime import UTC, datetime

from libraries.schemas.common import EventEnvelope, Severity, generate_event_id, utcnow


class TestGenerateEventId:
    def test_returns_string_with_prefix(self) -> None:
        event_id = generate_event_id()
        assert isinstance(event_id, str)
        assert event_id.startswith("evt_")
        assert len(event_id) > 4

    def test_generates_unique_ids(self) -> None:
        ids = {generate_event_id() for _ in range(100)}
        assert len(ids) == 100


class TestUtcnow:
    def test_returns_utc_datetime(self) -> None:
        now = utcnow()
        assert isinstance(now, datetime)
        assert now.tzinfo == UTC


class TestEventEnvelope:
    def test_creates_with_defaults(self) -> None:
        event = EventEnvelope(
            event_type="TEST_EVENT",
            source="test",
            producer="test_producer",
        )
        assert event.event_type == "TEST_EVENT"
        assert event.source == "test"
        assert event.event_type == "TEST_EVENT"
        assert event.event_version == "1.0"
        assert event.severity == Severity.INFO
        assert event.payload == {}
        assert event.metadata == {}
        assert event.event_id.startswith("evt_")
        assert event.timestamp is not None

    def test_creates_with_full_data(self) -> None:
        ts = datetime(2025, 1, 1, tzinfo=UTC)
        event = EventEnvelope(
            event_type="LOGIN_SUCCESS",
            source="auth_service",
            producer="auth_v2",
            payload={"user_id": "u123"},
            severity=Severity.INFO,
            metadata={"ip": "10.0.0.1"},
            tenant_id="tenant_1",
            trace_id="trace_abc",
            run_id="run_123",
            agent_id="agent_1",
            session_id="session_1",
            timestamp=ts,
        )
        assert event.tenant_id == "tenant_1"
        assert event.run_id == "run_123"
        assert event.agent_id == "agent_1"
        assert event.payload == {"user_id": "u123"}

    def test_serialization_roundtrip(self) -> None:
        event = EventEnvelope(
            event_type="TOOL_CALL",
            source="agent_runtime",
            producer="agent_v1",
            payload={"tool": "search"},
        )
        data = event.model_dump()
        restored = EventEnvelope.model_validate(data)
        assert restored.event_id == event.event_id
        assert restored.event_type == event.event_type

    def test_json_serialization(self) -> None:
        event = EventEnvelope(
            event_type="TEST",
            source="test",
            producer="test",
        )
        json_str = event.model_dump_json()
        restored = EventEnvelope.model_validate_json(json_str)
        assert restored.event_id == event.event_id
