from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from libraries.database.models import EventRecord
    from libraries.schemas.common import EventEnvelope


class EventRepository(ABC):
    @abstractmethod
    async def create_event(self, event: EventEnvelope) -> EventRecord:
        """Persist an event. Raises DuplicateEventError if event_id already exists."""
        ...

    @abstractmethod
    async def get_event_by_id(self, event_id: str) -> EventRecord | None:
        """Retrieve an event by its ID. Returns None if not found."""
        ...

    @abstractmethod
    async def event_exists(self, event_id: str) -> bool:
        """Check if an event with the given ID exists."""
        ...
