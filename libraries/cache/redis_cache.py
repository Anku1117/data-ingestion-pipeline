from __future__ import annotations

from libraries.cache.base import Cache
from libraries.logging.logging import get_logger

logger = get_logger(__name__)


class RedisCache(Cache):
    """Redis cache backend for production use."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._redis_url = redis_url
        self._client = None
        logger.info("RedisCache initialized url=%s", redis_url)

    async def start(self) -> None:
        try:
            import redis.asyncio as aioredis

            self._client = aioredis.from_url(self._redis_url, decode_responses=True)
            logger.info("RedisCache connected")
        except ImportError:
            logger.warning("redis package not installed")
            raise
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", str(e))
            raise

    async def stop(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> str | None:
        if not self._client:
            return None
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        if not self._client:
            return
        if ttl:
            await self._client.setex(key, ttl, value)
        else:
            await self._client.set(key, value)

    async def delete(self, key: str) -> None:
        if self._client:
            await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        if not self._client:
            return False
        return await self._client.exists(key) > 0

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            return await self._client.ping()
        except Exception:
            return False
