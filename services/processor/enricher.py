from __future__ import annotations

from datetime import UTC, datetime

from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope, Severity
from services.processor.base import Enricher

logger = get_logger(__name__)

SEVERITY_MAP = {
    "debug": Severity.DEBUG,
    "info": Severity.INFO,
    "warning": Severity.WARNING,
    "warn": Severity.WARNING,
    "error": Severity.ERROR,
    "critical": Severity.CRITICAL,
    "fatal": Severity.CRITICAL,
}

SOURCE_CATEGORY_MAP = {
    "auth_service": "security",
    "auth_v1": "security",
    "auth_v2": "security",
    "firewall": "security",
    "network": "security",
    "agent_runtime": "agent",
    "agent_v1": "agent",
    "agent_v2": "agent",
    "web_app": "application",
    "api_gateway": "application",
    "database": "infrastructure",
    "cache": "infrastructure",
}


class EventEnricher(Enricher):
    """Enriches events with derived metadata."""

    def enrich(self, event: EventEnvelope) -> EventEnvelope:
        metadata = dict(event.metadata)

        metadata["enriched_at"] = datetime.now(UTC).isoformat()
        metadata["source_category"] = SOURCE_CATEGORY_MAP.get(event.source, "unknown")
        metadata["event_type_upper"] = event.event_type.upper()
        metadata["has_agent_context"] = event.agent_id is not None
        metadata["has_run_context"] = event.run_id is not None

        if event.severity == Severity.CRITICAL or event.severity == Severity.ERROR:
            metadata["requires_attention"] = True

        if "ip_address" in event.payload:
            metadata["has_ip_context"] = True

        if "user_id" in event.payload:
            metadata["has_user_context"] = True

        return event.model_copy(update={"metadata": metadata})
