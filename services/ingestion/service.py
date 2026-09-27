from __future__ import annotations

from typing import TYPE_CHECKING

from libraries.database.repositories import DuplicateEventError
from libraries.logging.logging import get_logger
from libraries.observability.metrics import get_metrics, timed
from libraries.schemas.common import EventEnvelope

if TYPE_CHECKING:
    from libraries.database.repositories.base import EventRepository

logger = get_logger(__name__)


class EventService:
    def __init__(self, repository: EventRepository) -> None:
        self._repository = repository

    @timed("service.create_event")
    async def create_event(self, event: EventEnvelope) -> EventEnvelope:
        metrics = get_metrics()
        try:
            existing = await self._repository.event_exists(event.event_id)
            if existing:
                metrics.increment("duplicate_events_total")
                logger.info("Duplicate event detected event_id=%s", event.event_id)
                raise DuplicateEventError(event.event_id)
            await self._repository.create_event(event)
            return event
        except DuplicateEventError:
            raise
        except Exception as e:
            metrics.increment("database_operation_failure_total")
            logger.error("Failed to persist event event_id=%s error=%s", event.event_id, str(e))
            raise

    async def get_event(self, event_id: str) -> EventEnvelope | None:
        record = await self._repository.get_event_by_id(event_id)
        if record is None:
            return None
        return EventEnvelope(
            event_id=record.event_id,
            event_version=record.event_version,
            event_type=record.event_type,
            timestamp=record.timestamp,
            source=record.source,
            producer=record.producer,
            tenant_id=record.tenant_id,
            trace_id=record.trace_id,
            run_id=record.run_id,
            task_id=record.task_id,
            agent_id=record.agent_id,
            session_id=record.session_id,
            severity=record.severity,
            payload=record.payload,
            metadata=record.metadata_,
            schema_version=record.schema_version,
        )
