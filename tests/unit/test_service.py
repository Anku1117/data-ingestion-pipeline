from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libraries.database.models import Base
from libraries.database.repositories.event_repository import (
    DuplicateEventError,
    SQLAlchemyEventRepository,
)
from libraries.schemas.common import EventEnvelope
from services.ingestion.service import EventService


@pytest.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture
def event_service(db_session) -> EventService:
    repo = SQLAlchemyEventRepository(db_session)
    return EventService(repo)


@pytest.mark.asyncio
class TestEventService:
    async def test_create_event(self, event_service) -> None:
        event = EventEnvelope(
            event_type="TEST",
            source="test_source",
            producer="test_producer",
        )
        result = await event_service.create_event(event)
        assert result.event_id == event.event_id

    async def test_duplicate_event_raises(self, event_service) -> None:
        event = EventEnvelope(
            event_type="TEST",
            source="test_source",
            producer="test_producer",
        )
        await event_service.create_event(event)
        with pytest.raises(DuplicateEventError):
            await event_service.create_event(event)

    async def test_get_event(self, event_service) -> None:
        event = EventEnvelope(
            event_type="TEST",
            source="test_source",
            producer="test_producer",
        )
        await event_service.create_event(event)
        found = await event_service.get_event(event.event_id)
        assert found is not None
        assert found.event_id == event.event_id

    async def test_get_event_missing(self, event_service) -> None:
        found = await event_service.get_event("nonexistent")
        assert found is None
