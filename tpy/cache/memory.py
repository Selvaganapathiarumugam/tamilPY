"""
In-process memory cache store.
"""

from __future__ import annotations

import time
from typing import Any

from tpy.cache.store import CacheStore


class MemoryStore(CacheStore):
    """Dict-backed cache for tests and single-process apps."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float | None]] = {}

    def get(self, key: str) -> Any | None:
        item = self._data.get(key)
        if item is None:
            return None
        value, expires = item
        if expires is not None and time.time() >= expires:
            self._data.pop(key, None)
            return None
        return value

    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires = None if ttl is None else time.time() + ttl
        self._data[key] = (value, expires)

    def forget(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    def flush(self) -> None:
        self._data.clear()

    def has(self, key: str) -> bool:
        return self.get(key) is not None
