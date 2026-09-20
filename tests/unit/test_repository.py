from __future__ import annotations

import pytest

from libraries.database.repositories.event_repository import (
    SQLAlchemyEventRepository,
)
from libraries.schemas.common import EventEnvelope


@pytest.mark.asyncio
class TestSQLAlchemyEventRepository:
    async def test_create_event(self, db_session) -> None:
        repo = SQLAlchemyEventRepository(db_session)
        event = EventEnvelope(
            event_type="TEST",
            source="test_source",
            producer="test_producer",
            payload={"key": "value"},
        )
        record = await repo.create_event(event)
        assert record.event_id == event.event_id
        assert record.event_type == "TEST"
        assert record.source == "test_source"

    async def test_get_event_by_id(self, db_session) -> None:
        repo = SQLAlchemyEventRepository(db_session)
        event = EventEnvelope(
            event_type="TEST",
            source="test_source",
            producer="test_producer",
        )
        await repo.create_event(event)
        found = await repo.get_event_by_id(event.event_id)
        assert found is not None
        assert found.event_id == event.event_id

    async def test_get_event_missing(self, db_session) -> None:
        repo = SQLAlchemyEventRepository(db_session)
        found = await repo.get_event_by_id("nonexistent")
        assert found is None

    async def test_event_exists(self, db_session) -> None:
        repo = SQLAlchemyEventRepository(db_session)
        event = EventEnvelope(
            event_type="TEST",
            source="test_source",
            producer="test_producer",
        )
        await repo.create_event(event)
        assert await repo.event_exists(event.event_id) is True
        assert await repo.event_exists("nonexistent") is False

    async def test_create_event_with_optional_fields(self, db_session) -> None:
        repo = SQLAlchemyEventRepository(db_session)
        event = EventEnvelope(
            event_type="AGENT_STEP",
            source="agent_runtime",
            producer="agent_v1",
            tenant_id="tenant_1",
            run_id="run_123",
            agent_id="agent_1",
            session_id="session_1",
            task_id="task_1",
            payload={"step": 1},
            metadata={"version": "1.0"},
        )
        record = await repo.create_event(event)
        assert record.tenant_id == "tenant_1"
        assert record.run_id == "run_123"
        assert record.agent_id == "agent_1"
        assert record.session_id == "session_1"
        assert record.task_id == "task_1"
        assert record.payload == {"step": 1}
        assert record.metadata_ == {"version": "1.0"}
