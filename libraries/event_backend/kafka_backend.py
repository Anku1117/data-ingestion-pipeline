from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from libraries.event_backend.base import EventBackend
from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope

logger = get_logger(__name__)


class KafkaEventBackend(EventBackend):
    """Kafka event backend using aiokafka.

    Requires a running Kafka broker. Falls back gracefully if unavailable.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._producer: Any = None
        self._consumer: Any = None
        self._running = False
        logger.info("KafkaEventBackend initialized servers=%s", bootstrap_servers)

    async def start(self) -> None:
        try:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            await self._producer.start()
            self._running = True
            logger.info("KafkaEventBackend started")
        except ImportError:
            logger.warning("aiokafka not installed, Kafka backend unavailable")
            raise
        except Exception as e:
            logger.error("Failed to start Kafka backend: %s", str(e))
            raise

    async def stop(self) -> None:
        self._running = False
        if self._producer:
            await self._producer.stop()
        if self._consumer:
            await self._consumer.stop()
        logger.info("KafkaEventBackend stopped")

    async def publish(self, topic: str, event: EventEnvelope) -> None:
        if not self._producer:
            raise RuntimeError("Kafka producer not initialized")
        event_data = event.model_dump(mode="json")
        await self._producer.send(topic, value=event_data)
        logger.debug("Published event %s to Kafka topic %s", event.event_id, topic)

    async def publish_batch(self, topic: str, events: list[EventEnvelope]) -> int:
        if not self._producer:
            raise RuntimeError("Kafka producer not initialized")
        for event in events:
            event_data = event.model_dump(mode="json")
            await self._producer.send(topic, value=event_data)
        return len(events)

    async def subscribe(
        self, topics: list[str], group_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        try:
            from aiokafka import AIOKafkaConsumer

            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self._bootstrap_servers,
                group_id=group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            )
            await consumer.start()
            self._consumer = consumer
            logger.info("Kafka consumer started topics=%s group=%s", topics, group_id)

            try:
                async for msg in consumer:
                    yield msg.value
            finally:
                await consumer.stop()
        except ImportError:
            logger.error("aiokafka not installed")
            return
        except Exception as e:
            logger.error("Kafka consumer error: %s", str(e))
            return

    async def health_check(self) -> bool:
        if not self._producer:
            return False
        try:
            await self._producer.send_and_wait(
                "__health_check", value=b"ping"
            )
            return True
        except Exception:
            return False
