from __future__ import annotations

from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope
from services.processor.base import Router

logger = get_logger(__name__)

ROUTING_RULES = {
    "security": {
        "event_types": {
            "LOGIN_SUCCESS",
            "LOGIN_FAILED",
            "LOGOUT",
            "PERMISSION_CHANGED",
            "FIREWALL_BLOCK",
            "INTRUSION_ATTEMPT",
            "MALWARE_DETECTED",
        },
        "sources": {"auth_service", "auth_v1", "auth_v2", "firewall", "network"},
        "topic": "dip-security",
    },
    "agent": {
        "event_types": {
            "AGENT_STEP",
            "AGENT_MODEL_CALL",
            "AGENT_TOOL_CALL",
            "AGENT_TOOL_RESULT",
            "AGENT_TASK_COMPLETED",
            "AGENT_TASK_FAILED",
            "AGENT_RETRIEVAL",
            "AGENT_EVALUATION",
        },
        "sources": {"agent_runtime", "agent_v1", "agent_v2"},
        "topic": "dip-agent",
    },
}

DEFAULT_TOPIC = "dip-events"
DLQ_TOPIC = "dip-dlq"


class EventRouter(Router):
    """Routes events by type, source, and severity to appropriate topics."""

    def route(self, event: EventEnvelope) -> str:
        for category, rule in ROUTING_RULES.items():
            if event.event_type in rule["event_types"]:
                logger.debug(
                    "Routed event_id=%s to topic=%s category=%s",
                    event.event_id,
                    rule["topic"],
                    category,
                )
                return rule["topic"]

            if event.source in rule["sources"]:
                logger.debug(
                    "Routed event_id=%s to topic=%s category=%s",
                    event.event_id,
                    rule["topic"],
                    category,
                )
                return rule["topic"]

        return DEFAULT_TOPIC

    def route_invalid(self, event: EventEnvelope) -> str:
        return DLQ_TOPIC
