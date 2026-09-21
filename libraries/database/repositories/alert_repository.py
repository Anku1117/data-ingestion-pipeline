from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from libraries.database.alert_models import AlertRecord
from libraries.database.repositories.alert_base import AlertRepository
from libraries.logging.logging import get_logger
from services.detector.models import ThreatAlert, ThreatSeverity, ThreatType

logger = get_logger(__name__)


def _record_to_alert(record: AlertRecord) -> ThreatAlert:
    return ThreatAlert(
        alert_id=record.alert_id,
        threat_type=ThreatType(record.threat_type),
        severity=ThreatSeverity(record.severity),
        confidence=record.confidence,
        timestamp=record.timestamp,
        source=record.source,
        description=record.description,
        event_ids=record.event_ids or [],
        evidence=record.evidence or {},
        metadata=record.metadata_ or {},
        acknowledged=record.acknowledged,
    )


def _alert_to_record(alert: ThreatAlert) -> AlertRecord:
    return AlertRecord(
        alert_id=alert.alert_id,
        threat_type=alert.threat_type.value,
        severity=alert.severity.value,
        confidence=alert.confidence,
        source=alert.source,
        description=alert.description,
        event_ids=alert.event_ids,
        evidence=alert.evidence,
        metadata_=alert.metadata,
        acknowledged=alert.acknowledged,
        timestamp=alert.timestamp,
    )


class SQLAlchemyAlertRepository(AlertRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, alert: ThreatAlert) -> None:
        record = _alert_to_record(alert)
        self._session.add(record)
        await self._session.flush()
        logger.debug("Saved alert %s", alert.alert_id)

    async def save_batch(self, alerts: list[ThreatAlert]) -> None:
        records = [_alert_to_record(a) for a in alerts]
        for record in records:
            self._session.add(record)
        await self._session.flush()
        logger.debug("Saved %d alerts in batch", len(alerts))

    async def get_by_id(self, alert_id: str) -> ThreatAlert | None:
        result = await self._session.execute(
            select(AlertRecord).where(AlertRecord.alert_id == alert_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return _record_to_alert(record)

    async def list_alerts(
        self,
        threat_type: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        stmt = select(AlertRecord)
        count_stmt = select(func.count()).select_from(AlertRecord)

        if threat_type:
            stmt = stmt.where(AlertRecord.threat_type == threat_type)
            count_stmt = count_stmt.where(AlertRecord.threat_type == threat_type)
        if severity:
            stmt = stmt.where(AlertRecord.severity == severity)
            count_stmt = count_stmt.where(AlertRecord.severity == severity)

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(AlertRecord.timestamp.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        records = result.scalars().all()

        return {
            "total": total,
            "alerts": [_record_to_alert(r).model_dump(mode="json") for r in records],
            "limit": limit,
            "offset": offset,
        }

    async def count(self, threat_type: str | None = None, severity: str | None = None) -> int:
        stmt = select(func.count()).select_from(AlertRecord)
        if threat_type:
            stmt = stmt.where(AlertRecord.threat_type == threat_type)
        if severity:
            stmt = stmt.where(AlertRecord.severity == severity)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def acknowledge(self, alert_id: str) -> bool:
        result = await self._session.execute(
            select(AlertRecord).where(AlertRecord.alert_id == alert_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return False
        record.acknowledged = True
        await self._session.flush()
        logger.info("Acknowledged alert %s", alert_id)
        return True

    async def delete_old(self, days: int) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self._session.execute(
            delete(AlertRecord).where(AlertRecord.created_at < cutoff)
        )
        deleted = result.rowcount
        await self._session.flush()
        if deleted > 0:
            logger.info("Deleted %d alerts older than %d days", deleted, days)
        return deleted
