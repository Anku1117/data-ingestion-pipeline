from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libraries.database.agent_models import (
    AgentEvaluationRecord,
    AgentRunRecord,
    AgentStepRecord,
    AgentTaskRecord,
)
from libraries.database.alert_models import AlertRecord
from libraries.database.models import Base
from libraries.database.repositories import (
    SQLAlchemyAlertRepository,
    SQLAlchemyAgentEvaluationRepository,
    SQLAlchemyAgentRunRepository,
    SQLAlchemyAgentStepRepository,
    SQLAlchemyAgentTaskRepository,
)
from services.agent_data.service import AgentDataService
from services.detector.engine import DetectionEngine
from services.detector.models import ThreatAlert, ThreatSeverity, ThreatType


@pytest.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(async_engine):
    return async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.mark.asyncio
class TestAlertPersistence:
    async def test_save_alert(self, session_factory) -> None:
        async with session_factory() as session:
            repo = SQLAlchemyAlertRepository(session)
            alert = ThreatAlert(
                threat_type=ThreatType.BRUTE_FORCE,
                severity=ThreatSeverity.HIGH,
                confidence=0.95,
                source="auth_service",
                description="5 failed login attempts from 10.0.0.1",
                event_ids=["evt_001", "evt_002"],
                evidence={"ip": "10.0.0.1", "count": 5},
            )
            await repo.save(alert)
            await session.commit()

            retrieved = await repo.get_by_id(alert.alert_id)
            assert retrieved is not None
            assert retrieved.threat_type == ThreatType.BRUTE_FORCE
            assert retrieved.severity == ThreatSeverity.HIGH
            assert retrieved.confidence == 0.95
            assert retrieved.event_ids == ["evt_001", "evt_002"]

    async def test_save_batch(self, session_factory) -> None:
        async with session_factory() as session:
            repo = SQLAlchemyAlertRepository(session)
            alerts = [
                ThreatAlert(
                    threat_type=ThreatType.PORT_SCAN,
                    severity=ThreatSeverity.MEDIUM,
                    confidence=0.8,
                    source="network_monitor",
                    description=f"Port scan detected from 10.0.0.{i}",
                )
                for i in range(5)
            ]
            await repo.save_batch(alerts)
            await session.commit()

            count = await repo.count()
            assert count == 5

    async def test_list_with_filters(self, session_factory) -> None:
        async with session_factory() as session:
            repo = SQLAlchemyAlertRepository(session)
            await repo.save(
                ThreatAlert(
                    threat_type=ThreatType.BRUTE_FORCE,
                    severity=ThreatSeverity.HIGH,
                    confidence=0.9,
                    source="auth",
                    description="bf",
                )
            )
            await repo.save(
                ThreatAlert(
                    threat_type=ThreatType.PORT_SCAN,
                    severity=ThreatSeverity.LOW,
                    confidence=0.5,
                    source="network",
                    description="ps",
                )
            )
            await session.commit()

            result = await repo.list_alerts(threat_type="brute_force")
            assert result["total"] == 1

            result = await repo.list_alerts(severity="low")
            assert result["total"] == 1

            result = await repo.list_alerts()
            assert result["total"] == 2

    async def test_acknowledge(self, session_factory) -> None:
        async with session_factory() as session:
            repo = SQLAlchemyAlertRepository(session)
            alert = ThreatAlert(
                threat_type=ThreatType.HIGH_REQUEST_FREQUENCY,
                severity=ThreatSeverity.MEDIUM,
                confidence=0.7,
                source="api_gateway",
                description="High request frequency",
            )
            await repo.save(alert)
            await session.commit()

            result = await repo.acknowledge(alert.alert_id)
            assert result is True

            retrieved = await repo.get_by_id(alert.alert_id)
            assert retrieved is not None
            assert retrieved.acknowledged is True

    async def test_delete_old(self, session_factory) -> None:
        async with session_factory() as session:
            repo = SQLAlchemyAlertRepository(session)
            await repo.save(
                ThreatAlert(
                    threat_type=ThreatType.BRUTE_FORCE,
                    severity=ThreatSeverity.HIGH,
                    confidence=0.9,
                    source="auth",
                    description="old alert",
                )
            )
            await session.commit()

            deleted = await repo.delete_old(days=0)
            assert deleted == 1

            count = await repo.count()
            assert count == 0

    async def test_detection_engine_with_repository(self, session_factory) -> None:
        async with session_factory() as session:
            repo = SQLAlchemyAlertRepository(session)
            engine = DetectionEngine(alert_repository=repo)

            events = [
                {
                    "event_type": "LOGIN_FAILED",
                    "source": "auth",
                    "timestamp": f"2026-01-01T00:00:{i:02d}Z",
                }
                for i in range(10)
            ]
            results = engine.evaluate(events)
            assert len(results) > 0
