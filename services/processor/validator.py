from __future__ import annotations

from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope, Severity
from services.processor.base import ValidationResult, Validator

logger = get_logger(__name__)

VALID_EVENT_TYPES = {
    "LOGIN_SUCCESS",
    "LOGIN_FAILED",
    "LOGOUT",
    "USER_CREATED",
    "USER_DELETED",
    "PERMISSION_CHANGED",
    "DATA_ACCESS",
    "FILE_DOWNLOAD",
    "API_CALL",
    "SYSTEM_ERROR",
    "HEALTH_CHECK",
    "AGENT_STEP",
    "AGENT_MODEL_CALL",
    "AGENT_TOOL_CALL",
    "AGENT_TOOL_RESULT",
    "AGENT_TASK_COMPLETED",
    "AGENT_TASK_FAILED",
    "AGENT_RETRIEVAL",
    "AGENT_EVALUATION",
    "NETWORK_CONNECTION",
    "FIREWALL_BLOCK",
    "INTRUSION_ATTEMPT",
    "MALWARE_DETECTED",
    "DNS_QUERY",
    "HTTP_REQUEST",
    "DATABASE_QUERY",
    "CACHE_OPERATION",
}

VALID_SEVERITY = {s.value for s in Severity}


class EventValidator(Validator):
    """Validates events against canonical schema rules."""

    def validate(self, event: EventEnvelope) -> ValidationResult:
        errors: list[str] = []

        if not event.event_type:
            errors.append("event_type is required")
            return ValidationResult.INVALID

        if not event.source:
            errors.append("source is required")
            return ValidationResult.INVALID

        if not event.producer:
            errors.append("producer is required")
            return ValidationResult.INVALID

        if event.severity.value not in VALID_SEVERITY:
            errors.append(f"invalid severity: {event.severity}")
            return ValidationResult.INVALID

        if not event.event_id:
            errors.append("event_id is required")
            return ValidationResult.INVALID

        if not event.timestamp:
            errors.append("timestamp is required")
            return ValidationResult.INVALID

        if errors:
            logger.warning("Validation failed event_id=%s errors=%s", event.event_id, errors)
            return ValidationResult.INVALID

        return ValidationResult.VALID
