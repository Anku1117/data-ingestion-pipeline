from __future__ import annotations

from fastapi import APIRouter

from libraries.configuration.settings import get_settings
from libraries.event_backend import get_event_backend
from libraries.logging.logging import get_logger
from libraries.observability.metrics import get_metrics
from libraries.search import get_search

logger = get_logger(__name__)
router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/status")
async def pipeline_status() -> dict:
    settings = get_settings()
    backend = get_event_backend()
    search = get_search()
    metrics = get_metrics()

    return {
        "status": "operational",
        "event_backend": {
            "type": settings.event_backend,
            "healthy": await backend.health_check(),
        },
        "search_backend": {
            "type": settings.search_backend,
            "healthy": await search.health_check(),
        },
        "metrics": {
            "events_received": metrics.get_counter("pipeline.events_received"),
            "events_processed": metrics.get_counter("pipeline.events_processed"),
            "validation_failed": metrics.get_counter("pipeline.validation_failed"),
            "duplicates_detected": metrics.get_counter("pipeline.duplicates_detected"),
            "threats_detected": metrics.get_counter("detector.threats_detected"),
        },
    }


@router.get("/stats")
async def pipeline_stats() -> dict:
    metrics = get_metrics()
    return {
        "pipeline": {
            "events_received": metrics.get_counter("pipeline.events_received"),
            "events_processed": metrics.get_counter("pipeline.events_processed"),
            "validation_failed": metrics.get_counter("pipeline.validation_failed"),
            "duplicates_detected": metrics.get_counter("pipeline.duplicates_detected"),
        },
        "detector": {
            "threats_detected": metrics.get_counter("detector.threats_detected"),
            "rule_errors": metrics.get_counter("detector.rule_errors"),
        },
        "database": {
            "events_persisted": metrics.get_counter("events_persisted_total"),
            "db_errors": metrics.get_counter("database_operation_failure_total"),
        },
    }
