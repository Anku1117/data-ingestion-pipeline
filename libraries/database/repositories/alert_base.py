from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from services.detector.models import ThreatAlert


class AlertRepository(ABC):
    @abstractmethod
    async def save(self, alert: ThreatAlert) -> None: ...

    @abstractmethod
    async def save_batch(self, alerts: list[ThreatAlert]) -> None: ...

    @abstractmethod
    async def get_by_id(self, alert_id: str) -> ThreatAlert | None: ...

    @abstractmethod
    async def list_alerts(
        self,
        threat_type: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def count(self, threat_type: str | None = None, severity: str | None = None) -> int: ...

    @abstractmethod
    async def acknowledge(self, alert_id: str) -> bool: ...

    @abstractmethod
    async def delete_old(self, days: int) -> int: ...
