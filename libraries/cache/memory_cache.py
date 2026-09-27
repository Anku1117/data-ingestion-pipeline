from __future__ import annotations

import time

from libraries.cache.base import Cache
from libraries.logging.logging import get_logger

logger = get_logger(__name__)


class MemoryCache(Cache):
    """In-memory cache for development and testing."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}
        self._last_prune = time.time()
        self._prune_interval = 60.0
        logger.info("MemoryCache initialized")

    def _prune_expired(self) -> None:
        now = time.time()
        if now - self._last_prune < self._prune_interval:
            return
        self._last_prune = now
        expired = [
            key
            for key, (_, expires_at) in self._store.items()
            if expires_at is not None and now > expires_at
        ]
        for key in expired:
            del self._store[key]
        if expired:
            logger.debug("Pruned %d expired cache entries", len(expired))

    async def get(self, key: str) -> str | None:
        self._prune_expired()
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.time() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self._prune_expired()
        expires_at = time.time() + ttl if ttl else None
        self._store[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def health_check(self) -> bool:
        return True
