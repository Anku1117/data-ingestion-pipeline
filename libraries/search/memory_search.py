from __future__ import annotations

from typing import Any

from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope
from libraries.search.base import SearchBackend

logger = get_logger(__name__)


class MemorySearchBackend(SearchBackend):
    """In-memory search backend for development and testing."""

    def __init__(self) -> None:
        self._events: dict[str, dict[str, Any]] = {}
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("MemorySearchBackend started")

    async def stop(self) -> None:
        self._running = False
        logger.info("MemorySearchBackend stopped")

    async def index_event(self, event: EventEnvelope) -> None:
        self._events[event.event_id] = event.model_dump(mode="json")

    async def index_events(self, events: list[EventEnvelope]) -> int:
        for event in events:
            await self.index_event(event)
        return len(events)

    async def get_event(self, event_id: str) -> dict[str, Any] | None:
        return self._events.get(event_id)

    async def search_events(
        self,
        query: str | None = None,
        event_type: str | None = None,
        source: str | None = None,
        severity: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        results = list(self._events.values())

        if event_type:
            results = [e for e in results if e.get("event_type") == event_type]
        if source:
            results = [e for e in results if e.get("source") == source]
        if severity:
            results = [e for e in results if e.get("severity") == severity]
        if agent_id:
            results = [e for e in results if e.get("agent_id") == agent_id]
        if run_id:
            results = [e for e in results if e.get("run_id") == run_id]

        total = len(results)
        page = results[offset : offset + limit]

        return {
            "total": total,
            "events": page,
            "limit": limit,
            "offset": offset,
        }

    async def delete_event(self, event_id: str) -> bool:
        if event_id in self._events:
            del self._events[event_id]
            return True
        return False

    async def health_check(self) -> bool:
        return self._running
