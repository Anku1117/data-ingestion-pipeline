from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from services.detector.models import DetectionResult, ThreatAlert


class DetectionRule(ABC):
    """Base class for threat detection rules."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def evaluate(self, events: list[dict[str, Any]]) -> DetectionResult: ...


class BruteForceRule(DetectionRule):
    """Detects repeated authentication failures from same source."""

    def __init__(self, threshold: int = 5, window_seconds: int = 300) -> None:
        self._threshold = threshold
        self._window_seconds = window_seconds

    @property
    def name(self) -> str:
        return "brute_force"

    @property
    def description(self) -> str:
        return f"Detects >={self._threshold} auth failures within {self._window_seconds}s"

    def evaluate(self, events: list[dict[str, Any]]) -> DetectionResult:
        auth_failures: dict[str, list[dict[str, Any]]] = {}

        for event in events:
            if event.get("event_type") == "LOGIN_FAILED":
                source = event.get("source", "unknown")
                if source not in auth_failures:
                    auth_failures[source] = []
                auth_failures[source].append(event)

        alerts: list[ThreatAlert] = []
        for source, failures in auth_failures.items():
            if len(failures) >= self._threshold:
                alert = ThreatAlert(
                    threat_type="brute_force",
                    severity="high" if len(failures) >= self._threshold * 2 else "medium",
                    confidence=min(1.0, len(failures) / (self._threshold * 2)),
                    source=source,
                    description=f"Detected {len(failures)} failed logins from {source}",
                    event_ids=[f.get("event_id", "") for f in failures],
                    evidence={"failure_count": len(failures), "threshold": self._threshold},
                )
                alerts.append(alert)

        return DetectionResult(
            detected=len(alerts) > 0,
            alerts=alerts,
            features={"auth_failure_sources": list(auth_failures.keys())},
            rule_name=self.name,
        )


class PortScanRule(DetectionRule):
    """Detects access to unusual number of destination ports."""

    def __init__(self, threshold: int = 10) -> None:
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "port_scan"

    @property
    def description(self) -> str:
        return f"Detects access to >={self._threshold} unique ports"

    def evaluate(self, events: list[dict[str, Any]]) -> DetectionResult:
        port_access: dict[str, set[str]] = {}

        for event in events:
            payload = event.get("payload", {})
            dest_port = payload.get("dest_port") or payload.get("destination_port")
            source_ip = payload.get("source_ip") or payload.get("ip_address", "unknown")

            if dest_port:
                if source_ip not in port_access:
                    port_access[source_ip] = set()
                port_access[source_ip].add(str(dest_port))

        alerts: list[ThreatAlert] = []
        for ip, ports in port_access.items():
            if len(ports) >= self._threshold:
                alert = ThreatAlert(
                    threat_type="port_scan",
                    severity="medium",
                    confidence=min(1.0, len(ports) / (self._threshold * 3)),
                    source=ip,
                    description=f"Detected access to {len(ports)} unique ports from {ip}",
                    evidence={"unique_ports": len(ports), "ports": list(ports)[:20]},
                )
                alerts.append(alert)

        return DetectionResult(
            detected=len(alerts) > 0,
            alerts=alerts,
            features={"port_scan_sources": list(port_access.keys())},
            rule_name=self.name,
        )


class HighRequestFrequencyRule(DetectionRule):
    """Detects abnormally high request frequency."""

    def __init__(self, threshold: int = 100) -> None:
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "high_request_frequency"

    @property
    def description(self) -> str:
        return f"Detects >={self._threshold} requests from same source"

    def evaluate(self, events: list[dict[str, Any]]) -> DetectionResult:
        source_counts: dict[str, int] = {}

        for event in events:
            source = event.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

        alerts: list[ThreatAlert] = []
        for source, count in source_counts.items():
            if count >= self._threshold:
                alert = ThreatAlert(
                    threat_type="high_request_frequency",
                    severity="medium",
                    confidence=min(1.0, count / (self._threshold * 5)),
                    source=source,
                    description=f"High request frequency: {count} events from {source}",
                    evidence={"request_count": count, "threshold": self._threshold},
                )
                alerts.append(alert)

        return DetectionResult(
            detected=len(alerts) > 0,
            alerts=alerts,
            features={"source_counts": source_counts},
            rule_name=self.name,
        )


class AuthenticationAnomalyRule(DetectionRule):
    """Detects unusual auth failure/success ratio."""

    def __init__(self, failure_ratio_threshold: float = 0.5) -> None:
        self._failure_ratio_threshold = failure_ratio_threshold

    @property
    def name(self) -> str:
        return "auth_anomaly"

    @property
    def description(self) -> str:
        return f"Detects auth failure ratio > {self._failure_ratio_threshold}"

    def evaluate(self, events: list[dict[str, Any]]) -> DetectionResult:
        auth_events = [
            e for e in events if e.get("event_type") in ("LOGIN_SUCCESS", "LOGIN_FAILED")
        ]

        if len(auth_events) < 5:
            return DetectionResult(detected=False, alerts=[], features={}, rule_name=self.name)

        failures = sum(1 for e in auth_events if e["event_type"] == "LOGIN_FAILED")
        ratio = failures / len(auth_events)

        if ratio >= self._failure_ratio_threshold:
            alert = ThreatAlert(
                threat_type="auth_anomaly",
                severity="high" if ratio >= 0.8 else "medium",
                confidence=ratio,
                source="auth_system",
                description=f"High auth failure ratio: {ratio:.1%} ({failures}/{len(auth_events)})",
                evidence={
                    "failure_ratio": ratio,
                    "total_auth_events": len(auth_events),
                    "failures": failures,
                },
            )
            return DetectionResult(
                detected=True,
                alerts=[alert],
                features={"failure_ratio": ratio, "total_auth": len(auth_events)},
                rule_name=self.name,
            )

        return DetectionResult(
            detected=False, alerts=[], features={"failure_ratio": ratio}, rule_name=self.name
        )
