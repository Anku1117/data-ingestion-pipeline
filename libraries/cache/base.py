from __future__ import annotations

from abc import ABC, abstractmethod


class Cache(ABC):
    """Abstract cache backend for deduplication and short-lived state."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
