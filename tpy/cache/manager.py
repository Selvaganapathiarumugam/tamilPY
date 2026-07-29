"""
High-level cache repository.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from tpy.cache.store import CacheStore

T = TypeVar("T")


class Cache:
    """
    Application-facing cache API over a ``CacheStore``.

    Mirrors common Laravel-style helpers: get/put/forever/remember/pull.
    """

    def __init__(self, store: CacheStore) -> None:
        self.store = store

    def get(self, key: str, default: Any = None) -> Any:
        """Return cached value or ``default``."""
        value = self.store.get(key)
        return default if value is None else value

    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store ``value`` for ``ttl`` seconds (``None`` = forever)."""
        self.store.put(key, value, ttl=ttl)

    def forever(self, key: str, value: Any) -> None:
        """Store ``value`` without expiry."""
        self.put(key, value, ttl=None)

    def add(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Store only when the key is missing. Return whether written."""
        if self.has(key):
            return False
        self.put(key, value, ttl=ttl)
        return True

    def has(self, key: str) -> bool:
        """Return whether ``key`` is present."""
        return self.store.has(key)

    def forget(self, key: str) -> bool:
        """Delete ``key``."""
        return self.store.forget(key)

    def flush(self) -> None:
        """Clear the entire store."""
        self.store.flush()

    def pull(self, key: str, default: Any = None) -> Any:
        """Get and delete ``key``."""
        value = self.get(key, default)
        self.forget(key)
        return value

    def remember(
        self,
        key: str,
        ttl: int | None,
        callback: Callable[[], T],
    ) -> T:
        """Return cached value or compute, store, and return ``callback()``."""
        value = self.store.get(key)
        if value is not None:
            return value  # type: ignore[return-value]
        value = callback()
        self.put(key, value, ttl=ttl)
        return value

    def remember_forever(self, key: str, callback: Callable[[], T]) -> T:
        """``remember`` without expiry."""
        return self.remember(key, None, callback)

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment an integer value (missing keys start at 0)."""
        current = self.get(key, 0)
        try:
            updated = int(current) + amount
        except (TypeError, ValueError):
            updated = amount
        self.put(key, updated)
        return updated

    def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement an integer value."""
        return self.increment(key, -amount)
