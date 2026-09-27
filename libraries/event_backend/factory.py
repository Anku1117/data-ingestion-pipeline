from __future__ import annotations

from libraries.configuration.settings import get_settings
from libraries.event_backend.base import EventBackend
from libraries.logging.logging import get_logger

logger = get_logger(__name__)

_backend: EventBackend | None = None


def get_event_backend() -> EventBackend:
    global _backend
    if _backend is not None:
        return _backend

    settings = get_settings()
    backend_type = getattr(settings, "event_backend", "memory")

    if backend_type == "kafka":
        try:
            from libraries.event_backend.kafka_backend import KafkaEventBackend

            _backend = KafkaEventBackend(
                bootstrap_servers=settings.kafka_bootstrap_servers,
            )
            logger.info("Using KafkaEventBackend")
        except ImportError as e:
            if settings.is_production:
                raise RuntimeError(
                    "Kafka backend requested but aiokafka is not installed. "
                    "Install it with: pip install aiokafka"
                ) from e
            logger.warning("aiokafka not installed, falling back to memory backend")
            from libraries.event_backend.memory_backend import MemoryEventBackend

            _backend = MemoryEventBackend()
    elif backend_type == "memory":
        from libraries.event_backend.memory_backend import MemoryEventBackend

        _backend = MemoryEventBackend()
        if settings.is_production:
            logger.warning(
                "Using MemoryEventBackend in production. "
                "This is not recommended for production use."
            )
        else:
            logger.info("Using MemoryEventBackend (development mode)")
    else:
        raise ValueError(f"Unknown event backend: {backend_type}")

    return _backend


async def start_event_backend() -> None:
    backend = get_event_backend()
    await backend.start()


async def stop_event_backend() -> None:
    global _backend
    if _backend is not None:
        await _backend.stop()
        _backend = None


def reset_event_backend() -> None:
    """Reset backend singleton. Used in tests."""
    global _backend
    _backend = None
