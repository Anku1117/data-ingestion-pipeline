from __future__ import annotations

import pytest
from pydantic import ValidationError

from libraries.schemas.common import EventEnvelope, Severity


class TestEventEnvelopeContract:
    """Contract tests for EventEnvelope schema boundaries."""

    def test_minimal_valid_event(self) -> None:
        event = EventEnvelope(
            event_type="TEST",
            source="test",
            producer="test",
        )
        assert event.event_type == "TEST"
        assert event.event_version == "1.0"
        assert event.severity == Severity.INFO
        assert event.event_id.startswith("evt_")
        assert event.trace_id.startswith("trace_")
        assert event.timestamp is not None

    def test_event_id_contract(self) -> None:
        event = EventEnvelope(event_type="T", source="s", producer="p")
        assert isinstance(event.event_id, str)
        assert len(event.event_id) > 4
        assert event.event_id.startswith("evt_")

    def test_trace_id_contract(self) -> None:
        event = EventEnvelope(event_type="T", source="s", producer="p")
        assert isinstance(event.trace_id, str)
        assert event.trace_id.startswith("trace_")

    def test_severity_enum_contract(self) -> None:
        for sev in Severity:
            event = EventEnvelope(event_type="T", source="s", producer="p", severity=sev)
            assert event.severity == sev

    def test_severity_invalid_contract(self) -> None:
        with pytest.raises(ValidationError):
            EventEnvelope(event_type="T", source="s", producer="p", severity="invalid")

    def test_payload_contract(self) -> None:
        event = EventEnvelope(
            event_type="T", source="s", producer="p",
            payload={"key": "value", "nested": {"a": 1}},
        )
        assert event.payload["key"] == "value"
        assert event.payload["nested"]["a"] == 1

    def test_metadata_contract(self) -> None:
        event = EventEnvelope(
            event_type="T", source="s", producer="p",
            metadata={"version": "2.0"},
        )
        assert event.metadata["version"] == "2.0"

    def test_agent_fields_contract(self) -> None:
        event = EventEnvelope(
            event_type="AGENT_STEP", source="agent_runtime", producer="agent_v1",
            agent_id="agent_1", run_id="run_123", session_id="sess_1", task_id="task_1",
        )
        assert event.agent_id == "agent_1"
        assert event.run_id == "run_123"
        assert event.session_id == "sess_1"
        assert event.task_id == "task_1"

    def test_serialization_roundtrip(self) -> None:
        event = EventEnvelope(
            event_type="TEST", source="s", producer="p",
            payload={"x": 1}, metadata={"y": 2},
            agent_id="a1", run_id="r1",
        )
        data = event.model_dump(mode="json")
        restored = EventEnvelope.model_validate(data)
        assert restored.event_id == event.event_id
        assert restored.agent_id == event.agent_id
        assert restored.payload == event.payload

    def test_json_roundtrip(self) -> None:
        event = EventEnvelope(event_type="T", source="s", producer="p")
        json_str = event.model_dump_json()
        restored = EventEnvelope.model_validate_json(json_str)
        assert restored.event_id == event.event_id
        assert restored.event_type == event.event_type

    def test_event_type_required(self) -> None:
        with pytest.raises(ValidationError):
            EventEnvelope(source="s", producer="p")

    def test_source_required(self) -> None:
        with pytest.raises(ValidationError):
            EventEnvelope(event_type="T", producer="p")

    def test_producer_required(self) -> None:
        with pytest.raises(ValidationError):
            EventEnvelope(event_type="T", source="s")
