from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from libraries.schemas.common import EventEnvelope


class SearchBackend(ABC):
    """Abstract search backend for event indexing and retrieval."""

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def index_event(self, event: EventEnvelope) -> None: ...

    @abstractmethod
    async def index_events(self, events: list[EventEnvelope]) -> int: ...

    @abstractmethod
    async def get_event(self, event_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
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
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_event(self, event_id: str) -> bool: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
