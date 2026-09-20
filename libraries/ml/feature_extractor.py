from __future__ import annotations

from typing import Any

from libraries.logging.logging import get_logger
from libraries.ml.models import FeatureVector

logger = get_logger(__name__)


class FeatureExtractor:
    """Extracts numeric features from events for anomaly detection."""

    def extract(self, events: list[dict[str, Any]]) -> FeatureVector:
        if not events:
            return FeatureVector()

        unique_users: set[str] = set()
        unique_ports: set[str] = set()
        unique_event_types: set[str] = set()
        total_payload_size = 0
        error_count = 0
        agent_steps = 0
        failed_logins = 0

        for event in events:
            payload = event.get("payload", {})
            event_type = event.get("event_type", "")

            unique_event_types.add(event_type)

            user_id = payload.get("user_id")
            if user_id:
                unique_users.add(str(user_id))

            dest_port = payload.get("dest_port") or payload.get("destination_port")
            if dest_port:
                unique_ports.add(str(dest_port))

            total_payload_size += len(str(payload))

            if event.get("severity") in ("error", "critical"):
                error_count += 1

            if event_type.startswith("AGENT_"):
                agent_steps += 1

            if event_type == "LOGIN_FAILED":
                failed_logins += 1

        total = len(events)
        minutes_span = 1.0

        return FeatureVector(
            events_per_minute=total / max(minutes_span, 1.0),
            failed_login_count=float(failed_logins),
            unique_users=float(len(unique_users)),
            unique_ports=float(len(unique_ports)),
            request_frequency=float(total),
            event_frequency=float(total),
            avg_payload_size=total_payload_size / max(total, 1),
            unique_event_types=float(len(unique_event_types)),
            error_ratio=error_count / max(total, 1),
            agent_step_count=float(agent_steps),
        )
