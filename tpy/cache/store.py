"""
Cache store contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CacheStore(ABC):
    """Low-level key/value cache backend."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Return the value for ``key``, or ``None`` if missing/expired."""

    @abstractmethod
    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store ``value`` under ``key`` for ``ttl`` seconds (None = forever)."""

    @abstractmethod
    def forget(self, key: str) -> bool:
        """Delete ``key``. Return whether it existed."""

    @abstractmethod
    def flush(self) -> None:
        """Remove all keys managed by this store."""

    @abstractmethod
    def has(self, key: str) -> bool:
        """Return whether ``key`` exists and is not expired."""
