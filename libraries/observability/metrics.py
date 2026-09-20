from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from libraries.logging.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class MetricsCollector:
    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._timers: dict[str, list[float]] = {}

    def increment(self, name: str, value: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + value

    def record_time(self, name: str, duration_ms: float) -> None:
        if name not in self._timers:
            self._timers[name] = []
        self._timers[name].append(duration_ms)

    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def get_timer_stats(self, name: str) -> dict[str, float]:
        values = self._timers.get(name, [])
        if not values:
            return {"count": 0, "avg_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}
        return {
            "count": len(values),
            "avg_ms": sum(values) / len(values),
            "min_ms": min(values),
            "max_ms": max(values),
        }

    def reset(self) -> None:
        self._counters.clear()
        self._timers.clear()


_metrics: MetricsCollector | None = None


def get_metrics() -> MetricsCollector:
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


def timed(metric_name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                get_metrics().record_time(metric_name, duration_ms)
                logger.debug("metric.%s %.2fms", metric_name, duration_ms)

        return wrapper  # type: ignore[return-value]

    return decorator
