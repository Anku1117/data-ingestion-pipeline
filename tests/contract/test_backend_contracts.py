from __future__ import annotations

import pytest

from libraries.cache.base import Cache
from libraries.cache.memory_cache import MemoryCache
from libraries.event_backend.base import EventBackend
from libraries.event_backend.memory_backend import MemoryEventBackend
from libraries.schemas.common import EventEnvelope
from libraries.search.base import SearchBackend
from libraries.search.memory_search import MemorySearchBackend


@pytest.mark.asyncio
class TestEventBackendContract:
    """Contract tests that every EventBackend implementation must satisfy."""

    @pytest.fixture
    async def backend(self):
        b = MemoryEventBackend()
        await b.start()
        yield b
        await b.stop()

    async def test_start_stop(self, backend: EventBackend) -> None:
        assert await backend.health_check() is True
        await backend.stop()
        assert await backend.health_check() is False

    async def test_publish_and_subscribe(self, backend: EventBackend) -> None:
        event = EventEnvelope(
            event_type="TEST",
            source="test",
            producer="test",
            payload={"key": "value"},
        )
        await backend.publish("test-topic", event)

    async def test_publish_batch(self, backend: EventBackend) -> None:
        events = [
            EventEnvelope(event_type="TEST", source="test", producer="test", payload={"i": i})
            for i in range(5)
        ]
        count = await backend.publish_batch("test-topic", events)
        assert count == 5

    async def test_health_check(self, backend: EventBackend) -> None:
        assert await backend.health_check() is True


@pytest.mark.asyncio
class TestSearchBackendContract:
    """Contract tests that every SearchBackend implementation must satisfy."""

    @pytest.fixture
    async def backend(self):
        b = MemorySearchBackend()
        await b.start()
        yield b
        await b.stop()

    async def test_index_and_get(self, backend: SearchBackend) -> None:
        event = EventEnvelope(
            event_type="LOGIN_FAILED",
            source="auth_service",
            producer="auth_v1",
            payload={"user_id": "u1"},
        )
        await backend.index_event(event)
        result = await backend.get_event(event.event_id)
        assert result is not None
        assert result["event_type"] == "LOGIN_FAILED"

    async def test_search_with_filters(self, backend: SearchBackend) -> None:
        for i in range(3):
            event = EventEnvelope(
                event_type="LOGIN_FAILED",
                source="auth_service",
                producer="auth_v1",
                payload={"i": i},
            )
            await backend.index_event(event)

        result = await backend.search_events(event_type="LOGIN_FAILED")
        assert result["total"] == 3

    async def test_delete_event(self, backend: SearchBackend) -> None:
        event = EventEnvelope(
            event_type="TEST",
            source="test",
            producer="test",
        )
        await backend.index_event(event)
        deleted = await backend.delete_event(event.event_id)
        assert deleted is True
        result = await backend.get_event(event.event_id)
        assert result is None

    async def test_search_empty(self, backend: SearchBackend) -> None:
        result = await backend.search_events()
        assert result["total"] == 0
        assert result["events"] == []

    async def test_health_check(self, backend: SearchBackend) -> None:
        assert await backend.health_check() is True


@pytest.mark.asyncio
class TestCacheContract:
    """Contract tests that every Cache implementation must satisfy."""

    @pytest.fixture
    async def cache(self):
        c = MemoryCache()
        yield c

    async def test_set_and_get(self, cache: Cache) -> None:
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    async def test_get_missing_key(self, cache: Cache) -> None:
        result = await cache.get("nonexistent")
        assert result is None

    async def test_delete(self, cache: Cache) -> None:
        await cache.set("key1", "value1")
        await cache.delete("key1")
        assert await cache.get("key1") is None

    async def test_exists(self, cache: Cache) -> None:
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("key2") is False

    async def test_overwrite(self, cache: Cache) -> None:
        await cache.set("key1", "value1")
        await cache.set("key1", "value2")
        result = await cache.get("key1")
        assert result == "value2"

    async def test_health_check(self, cache: Cache) -> None:
        assert await cache.health_check() is True
