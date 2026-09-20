from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from libraries.event_backend.base import EventBackend
from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope

logger = get_logger(__name__)


class MemoryEventBackend(EventBackend):
    """In-memory event backend for development and testing.

    NOT a production backend. Provides the same interface as Kafka
    for local development and unit tests.
    """

    def __init__(self) -> None:
        self._topics: dict[str, list[dict[str, Any]]] = {}
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any] | None]]] = {}
        self._running = False
        logger.info("MemoryEventBackend initialized")

    async def start(self) -> None:
        self._running = True
        logger.info("MemoryEventBackend started")

    async def stop(self) -> None:
        self._running = False
        for topic_subs in self._subscribers.values():
            for q in topic_subs:
                await q.put(None)
        logger.info("MemoryEventBackend stopped")

    async def publish(self, topic: str, event: EventEnvelope) -> None:
        if topic not in self._topics:
            self._topics[topic] = []
        event_data = event.model_dump(mode="json")
        self._topics[topic].append(event_data)

        for queue in self._subscribers.get(topic, []):
            await queue.put(event_data)

        logger.debug("Published event %s to topic %s", event.event_id, topic)

    async def publish_batch(self, topic: str, events: list[EventEnvelope]) -> int:
        for event in events:
            await self.publish(topic, event)
        return len(events)

    async def subscribe(
        self, topics: list[str], group_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        queues: list[asyncio.Queue[dict[str, Any] | None]] = []
        for topic in topics:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            q: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
            self._subscribers[topic].append(q)
            queues.append(q)

        logger.info("Subscribed to topics=%s group_id=%s", topics, group_id)

        try:
            while self._running:
                for q in queues:
                    try:
                        event_data = q.get_nowait()
                        if event_data is not None:
                            yield event_data
                    except asyncio.QueueEmpty:
                        pass
                await asyncio.sleep(0.01)
        finally:
            for topic, q in zip(topics, queues, strict=False):
                if q in self._subscribers.get(topic, []):
                    self._subscribers[topic].remove(q)

    async def health_check(self) -> bool:
        return self._running

    def get_topic_events(self, topic: str) -> list[dict[str, Any]]:
        return list(self._topics.get(topic, []))

    def get_all_events(self) -> dict[str, list[dict[str, Any]]]:
        return {t: list(e) for t, e in self._topics.items()}
