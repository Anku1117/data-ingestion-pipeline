from __future__ import annotations

from fastapi import APIRouter

from libraries.logging.logging import get_logger
from libraries.observability.metrics import get_metrics

logger = get_logger(__name__)
router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics_endpoint() -> dict:
    metrics = get_metrics()
    counters = {}
    timers = {}

    for name in list(metrics._counters.keys()):
        counters[name] = metrics.get_counter(name)

    for name in list(metrics._timers.keys()):
        timers[name] = metrics.get_timer_stats(name)

    return {
        "counters": counters,
        "timers": timers,
    }
