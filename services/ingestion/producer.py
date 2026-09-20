from __future__ import annotations

from typing import TYPE_CHECKING, Any

from libraries.logging.logging import get_logger
from libraries.observability.metrics import get_metrics, timed

if TYPE_CHECKING:
    from libraries.schemas.common import EventEnvelope

logger = get_logger(__name__)


class EventProducer:
    """Kafka event producer.

    Currently uses an in-memory buffer for Phase 1.
    Will be replaced with actual Kafka producer in Phase 5.
    """

    def __init__(self) -> None:
        self._buffer: list[dict[str, Any]] = []
        logger.info("EventProducer initialized (in-memory mode)")

    @timed("kafka.produce")
    async def produce(self, topic: str, event: EventEnvelope) -> None:
        event_data = event.model_dump(mode="json")
        self._buffer.append(event_data)
        get_metrics().increment("kafka.events_produced")
        logger.info(
            "Event produced to topic=%s event_id=%s event_type=%s",
            topic,
            event.event_id,
            event.event_type,
        )

    async def produce_batch(self, topic: str, events: list[EventEnvelope]) -> int:
        count = 0
        for event in events:
            await self.produce(topic, event)
            count += 1
        return count

    def get_buffer(self) -> list[dict[str, Any]]:
        return list(self._buffer)

    def clear_buffer(self) -> int:
        count = len(self._buffer)
        self._buffer.clear()
        return count


_producer: EventProducer | None = None


def get_producer() -> EventProducer:
    global _producer
    if _producer is None:
        _producer = EventProducer()
    return _producer
