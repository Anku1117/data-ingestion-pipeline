from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from libraries.database.models import EventRecord
from libraries.database.repositories.base import EventRepository
from libraries.logging.logging import get_logger
from libraries.observability.metrics import get_metrics, timed

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from libraries.schemas.common import EventEnvelope

logger = get_logger(__name__)


class DuplicateEventError(Exception):
    def __init__(self, event_id: str) -> None:
        self.event_id = event_id
        super().__init__(f"Event with id '{event_id}' already exists")


class SQLAlchemyEventRepository(EventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_record(self, event: EventEnvelope) -> EventRecord:
        return EventRecord(
            event_id=event.event_id,
            event_version=event.event_version,
            event_type=event.event_type,
            timestamp=event.timestamp,
            source=event.source,
            producer=event.producer,
            tenant_id=event.tenant_id,
            trace_id=event.trace_id,
            run_id=event.run_id,
            task_id=event.task_id,
            agent_id=event.agent_id,
            session_id=event.session_id,
            severity=event.severity.value,
            payload=event.payload,
            metadata_=event.metadata,
            schema_version=event.schema_version,
        )

    @timed("db.create_event")
    async def create_event(self, event: EventEnvelope) -> EventRecord:
        metrics = get_metrics()
        record = self._to_record(event)
        try:
            self._session.add(record)
            await self._session.flush()
            metrics.increment("events_persisted_total")
            logger.info(
                "Event persisted event_id=%s event_type=%s",
                event.event_id,
                event.event_type,
            )
            return record
        except Exception:
            metrics.increment("database_operation_failure_total")
            raise

    @timed("db.get_event_by_id")
    async def get_event_by_id(self, event_id: str) -> EventRecord | None:
        stmt = select(EventRecord).where(EventRecord.event_id == event_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @timed("db.event_exists")
    async def event_exists(self, event_id: str) -> bool:
        result = await self._session.execute(
            select(EventRecord.event_id).where(EventRecord.event_id == event_id).limit(1)
        )
        return result.scalar_one_or_none() is not None
