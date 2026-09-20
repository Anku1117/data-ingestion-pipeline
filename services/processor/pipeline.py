from __future__ import annotations

from libraries.event_backend import get_event_backend
from libraries.logging.logging import get_logger
from libraries.observability.metrics import get_metrics, timed
from libraries.schemas.common import EventEnvelope
from services.processor.base import ProcessingResult, ValidationResult
from services.processor.deduplicator import EventDeduplicator
from services.processor.enricher import EventEnricher
from services.processor.router import EventRouter
from services.processor.validator import EventValidator

logger = get_logger(__name__)


class ProcessingPipeline:
    """Event processing pipeline: validate -> enrich -> deduplicate -> route."""

    def __init__(self) -> None:
        self._validator = EventValidator()
        self._enricher = EventEnricher()
        self._deduplicator = EventDeduplicator()
        self._router = EventRouter()

    @timed("pipeline.process")
    async def process(self, event: EventEnvelope) -> ProcessingResult:
        metrics = get_metrics()
        metrics.increment("pipeline.events_received")

        validation = self._validator.validate(event)
        if validation != ValidationResult.VALID:
            metrics.increment("pipeline.validation_failed")
            return ProcessingResult(
                status=validation,
                event=event,
                errors=[f"Validation failed: {validation.value}"],
            )

        enriched = self._enricher.enrich(event)

        is_dup = await self._deduplicator.is_duplicate(enriched)
        if is_dup:
            metrics.increment("pipeline.duplicates_detected")
            return ProcessingResult(
                status=ValidationResult.INVALID,
                event=enriched,
                errors=["Duplicate event"],
            )

        await self._deduplicator.record(enriched)

        topic = self._router.route(enriched)

        backend = get_event_backend()
        await backend.publish(topic, enriched)

        metrics.increment("pipeline.events_processed")
        logger.info(
            "Event processed event_id=%s topic=%s status=processed",
            enriched.event_id,
            topic,
        )

        return ProcessingResult(
            status=ValidationResult.VALID,
            event=enriched,
            metadata={"topic": topic, "enriched": True},
        )

    async def process_batch(self, events: list[EventEnvelope]) -> list[ProcessingResult]:
        results = []
        for event in events:
            result = await self.process(event)
            results.append(result)
        return results
