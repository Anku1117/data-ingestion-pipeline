from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from libraries.schemas.common import EventEnvelope


class ValidationResult(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    RETRYABLE = "retryable"
    PERMANENT_FAILURE = "permanent_failure"


class ProcessingResult:
    def __init__(
        self,
        status: ValidationResult,
        event: EventEnvelope,
        errors: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.event = event
        self.errors = errors or []
        self.metadata = metadata or {}

    @property
    def is_valid(self) -> bool:
        return self.status == ValidationResult.VALID

    @property
    def should_dlq(self) -> bool:
        return self.status == ValidationResult.PERMANENT_FAILURE


class Validator(ABC):
    @abstractmethod
    def validate(self, event: EventEnvelope) -> ValidationResult:
        ...


class Transformer(ABC):
    @abstractmethod
    def transform(self, event: EventEnvelope) -> EventEnvelope:
        ...


class Enricher(ABC):
    @abstractmethod
    def enrich(self, event: EventEnvelope) -> EventEnvelope:
        ...


class Deduplicator(ABC):
    @abstractmethod
    async def is_duplicate(self, event: EventEnvelope) -> bool:
        ...

    @abstractmethod
    async def record(self, event: EventEnvelope) -> None:
        ...


class Router(ABC):
    @abstractmethod
    def route(self, event: EventEnvelope) -> str:
        ...
