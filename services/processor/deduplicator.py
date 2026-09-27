from __future__ import annotations

from libraries.cache import get_cache
from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope
from services.processor.base import Deduplicator

logger = get_logger(__name__)

DEDUP_TTL_SECONDS = 86400  # 24 hours


class EventDeduplicator(Deduplicator):
    """Deduplicates events by event_id using cache backend."""

    def __init__(self) -> None:
        self._cache = get_cache()

    async def is_duplicate(self, event: EventEnvelope) -> bool:
        key = f"dedup:{event.event_id}"
        exists = await self._cache.get(key)
        if exists is not None:
            logger.info("Duplicate event detected event_id=%s", event.event_id)
            return True
        return False

    async def record(self, event: EventEnvelope) -> None:
        key = f"dedup:{event.event_id}"
        await self._cache.set(key, "1", ttl=DEDUP_TTL_SECONDS)
