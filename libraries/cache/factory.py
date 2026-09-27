from __future__ import annotations

from libraries.cache.base import Cache
from libraries.configuration.settings import get_settings
from libraries.logging.logging import get_logger

logger = get_logger(__name__)

_cache: Cache | None = None


def get_cache() -> Cache:
    global _cache
    if _cache is not None:
        return _cache

    settings = get_settings()
    backend = getattr(settings, "cache_backend", "memory")

    if backend == "redis":
        try:
            from libraries.cache.redis_cache import RedisCache

            _cache = RedisCache(redis_url=settings.redis_url)
            logger.info("Using RedisCache")
        except ImportError as e:
            if settings.is_production:
                raise RuntimeError(
                    "Redis backend requested but redis package is not installed. "
                    "Install it with: pip install redis"
                ) from e
            logger.warning("redis package not installed, falling back to memory cache")
            from libraries.cache.memory_cache import MemoryCache

            _cache = MemoryCache()
    elif backend == "memory":
        from libraries.cache.memory_cache import MemoryCache

        _cache = MemoryCache()
        if settings.is_production:
            logger.warning(
                "Using MemoryCache in production. " "This is not recommended for production use."
            )
        else:
            logger.info("Using MemoryCache (development mode)")
    else:
        raise ValueError(f"Unknown cache backend: {backend}")

    return _cache


def reset_cache() -> None:
    global _cache
    _cache = None
