from __future__ import annotations

import time

from fastapi import HTTPException, Request, status

from libraries.cache import get_cache
from libraries.logging.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Simple sliding window rate limiter using the cache backend."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_second: int = 10,
    ) -> None:
        self._rpm = requests_per_minute
        self._rps = requests_per_second
        self._cache = get_cache()

    async def check(self, key: str) -> None:
        now = time.time()

        rpm_key = f"ratelimit:rpm:{key}:{int(now // 60)}"
        rps_key = f"ratelimit:rps:{key}:{int(now)}"

        rpm_count = await self._cache.get(rpm_key)
        rps_count = await self._cache.get(rps_key)

        rpm_val = int(rpm_count) if rpm_count else 0
        rps_val = int(rps_count) if rps_count else 0

        if rpm_val >= self._rpm:
            logger.warning("Rate limit exceeded (RPM) key=%s", key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "detail": f"Rate limit: {self._rpm} requests per minute",
                    "retry_after": 60 - (int(now) % 60),
                },
            )

        if rps_val >= self._rps:
            logger.warning("Rate limit exceeded (RPS) key=%s", key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "detail": f"Rate limit: {self._rps} requests per second",
                    "retry_after": 1,
                },
            )

        await self._cache.set(rpm_key, str(rpm_val + 1), ttl=120)
        await self._cache.set(rps_key, str(rps_val + 1), ttl=5)


_default_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter()
    return _default_limiter


async def rate_limit(request: Request) -> None:
    limiter = get_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    await limiter.check(f"ip:{client_ip}")
