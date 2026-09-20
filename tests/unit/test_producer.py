from __future__ import annotations

import pytest

from libraries.schemas.common import EventEnvelope
from services.ingestion.producer import EventProducer


@pytest.mark.asyncio
class TestEventProducer:
    async def test_produce_single_event(self) -> None:
        producer = EventProducer()
        event = EventEnvelope(
            event_type="TEST",
            source="test",
            producer="test",
        )
        await producer.produce("test-topic", event)
        buffer = producer.get_buffer()
        assert len(buffer) == 1
        assert buffer[0]["event_type"] == "TEST"

    async def test_produce_batch(self) -> None:
        producer = EventProducer()
        events = [
            EventEnvelope(event_type=f"EVENT_{i}", source="test", producer="test") for i in range(5)
        ]
        count = await producer.produce_batch("test-topic", events)
        assert count == 5
        assert len(producer.get_buffer()) == 5

    async def test_clear_buffer(self) -> None:
        producer = EventProducer()
        event = EventEnvelope(event_type="TEST", source="test", producer="test")
        await producer.produce("topic", event)
        cleared = producer.clear_buffer()
        assert cleared == 1
        assert len(producer.get_buffer()) == 0
