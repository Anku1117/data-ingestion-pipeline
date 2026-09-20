from __future__ import annotations

from typing import Any

from libraries.logging.logging import get_logger
from libraries.observability.metrics import get_metrics
from services.detector.models import DetectionResult, ThreatAlert
from services.detector.rules import (
    AuthenticationAnomalyRule,
    BruteForceRule,
    DetectionRule,
    HighRequestFrequencyRule,
    PortScanRule,
)

logger = get_logger(__name__)


class DetectionEngine:
    """Rule-based threat detection engine."""

    def __init__(self) -> None:
        self._rules: list[DetectionRule] = [
            BruteForceRule(threshold=5, window_seconds=300),
            PortScanRule(threshold=10),
            HighRequestFrequencyRule(threshold=100),
            AuthenticationAnomalyRule(failure_ratio_threshold=0.5),
        ]
        self._alerts: list[ThreatAlert] = []
        logger.info("DetectionEngine initialized with %d rules", len(self._rules))

    def add_rule(self, rule: DetectionRule) -> None:
        self._rules.append(rule)

    def evaluate(self, events: list[dict[str, Any]]) -> list[DetectionResult]:
        metrics = get_metrics()
        results: list[DetectionResult] = []

        for rule in self._rules:
            try:
                result = rule.evaluate(events)
                results.append(result)
                if result.detected:
                    metrics.increment("detector.threats_detected")
                    self._alerts.extend(result.alerts)
                    for alert in result.alerts:
                        logger.warning(
                            "Threat detected alert_id=%s type=%s severity=%s confidence=%.2f",
                            alert.alert_id,
                            alert.threat_type,
                            alert.severity,
                            alert.confidence,
                        )
            except Exception as e:
                logger.error("Rule %s failed: %s", rule.name, str(e))
                metrics.increment("detector.rule_errors")

        return results

    def get_alerts(
        self,
        threat_type: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        alerts = list(self._alerts)

        if threat_type:
            alerts = [a for a in alerts if a.threat_type == threat_type]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        total = len(alerts)
        page = alerts[offset : offset + limit]

        return {
            "total": total,
            "alerts": [a.model_dump(mode="json") for a in page],
            "limit": limit,
            "offset": offset,
        }

    def get_alert_by_id(self, alert_id: str) -> ThreatAlert | None:
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                return alert
        return None

    def get_rules(self) -> list[dict[str, str]]:
        return [{"name": r.name, "description": r.description} for r in self._rules]

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_alerts": len(self._alerts),
            "active_rules": len(self._rules),
            "rules": self.get_rules(),
        }
