from __future__ import annotations

import pytest

from libraries.schemas.common import EventEnvelope
from services.processor.base import ValidationResult
from services.processor.enricher import EventEnricher
from services.processor.pipeline import ProcessingPipeline
from services.processor.router import EventRouter
from services.processor.validator import EventValidator


@pytest.fixture
def pipeline() -> ProcessingPipeline:
    return ProcessingPipeline()


@pytest.fixture
def validator() -> EventValidator:
    return EventValidator()


@pytest.fixture
def enricher() -> EventEnricher:
    return EventEnricher()


@pytest.fixture
def router() -> EventRouter:
    return EventRouter()


class TestProcessorValidation:
    def test_valid_event(self, validator: EventValidator) -> None:
        event = EventEnvelope(event_type="LOGIN_FAILED", source="auth", producer="auth_v1")
        assert validator.validate(event) == ValidationResult.VALID

    def test_invalid_missing_type(self, validator: EventValidator) -> None:
        event = EventEnvelope(event_type="", source="auth", producer="auth_v1")
        assert validator.validate(event) == ValidationResult.INVALID

    def test_invalid_missing_source(self, validator: EventValidator) -> None:
        event = EventEnvelope(event_type="TEST", source="", producer="p")
        assert validator.validate(event) == ValidationResult.INVALID


class TestProcessorEnrichment:
    def test_enrichment_adds_metadata(self, enricher: EventEnricher) -> None:
        event = EventEnvelope(event_type="TEST", source="auth_service", producer="p")
        enriched = enricher.enrich(event)
        assert "enriched_at" in enriched.metadata
        assert enriched.metadata["source_category"] == "security"

    def test_agent_context_detected(self, enricher: EventEnricher) -> None:
        event = EventEnvelope(
            event_type="AGENT_STEP", source="agent_runtime", producer="p", agent_id="a1",
        )
        enriched = enricher.enrich(event)
        assert enriched.metadata["has_agent_context"] is True

    def test_user_context_detected(self, enricher: EventEnricher) -> None:
        event = EventEnvelope(
            event_type="TEST", source="s", producer="p", payload={"user_id": "u1"},
        )
        enriched = enricher.enrich(event)
        assert enriched.metadata["has_user_context"] is True


class TestProcessorRouting:
    def test_security_routing(self, router: EventRouter) -> None:
        event = EventEnvelope(event_type="LOGIN_FAILED", source="auth_service", producer="p")
        topic = router.route(event)
        assert topic == "dip-security"

    def test_agent_routing(self, router: EventRouter) -> None:
        event = EventEnvelope(event_type="AGENT_STEP", source="agent_runtime", producer="p")
        topic = router.route(event)
        assert topic == "dip-agent"

    def test_default_routing(self, router: EventRouter) -> None:
        event = EventEnvelope(event_type="HEALTH_CHECK", source="web_app", producer="p")
        topic = router.route(event)
        assert topic == "dip-events"

    def test_dlq_routing(self, router: EventRouter) -> None:
        event = EventEnvelope(event_type="INVALID", source="unknown", producer="p")
        topic = router.route_invalid(event)
        assert topic == "dip-dlq"


class TestProcessorPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_process_valid(self, pipeline: ProcessingPipeline) -> None:
        event = EventEnvelope(
            event_type="LOGIN_FAILED", source="auth_service", producer="auth_v1",
            payload={"user_id": "u1"},
        )
        result = await pipeline.process(event)
        assert result.is_valid
        assert "topic" in result.metadata

    @pytest.mark.asyncio
    async def test_pipeline_rejects_invalid(self, pipeline: ProcessingPipeline) -> None:
        event = EventEnvelope(event_type="", source="auth", producer="p")
        result = await pipeline.process(event)
        assert not result.is_valid

    @pytest.mark.asyncio
    async def test_pipeline_batch(self, pipeline: ProcessingPipeline) -> None:
        events = [
            EventEnvelope(event_type="TEST", source="s", producer="p")
            for _ in range(5)
        ]
        results = await pipeline.process_batch(events)
        assert len(results) == 5
        assert all(r.is_valid for r in results)
