from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope

logger = get_logger(__name__)


class EventBackend(ABC):
    """Abstract event streaming backend."""

    @abstractmethod
    async def start(self) -> None:
        """Initialize the backend."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully shut down the backend."""
        ...

    @abstractmethod
    async def publish(self, topic: str, event: EventEnvelope) -> None:
        """Publish a single event to a topic."""
        ...

    @abstractmethod
    async def publish_batch(self, topic: str, events: list[EventEnvelope]) -> int:
        """Publish multiple events. Returns count published."""
        ...

    @abstractmethod
    async def subscribe(
        self, topics: list[str], group_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Subscribe to topics and yield events."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the backend is healthy."""
        ...
