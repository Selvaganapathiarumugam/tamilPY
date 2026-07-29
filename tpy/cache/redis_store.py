"""
Redis cache store (optional dependency).
"""

from __future__ import annotations

import pickle
from typing import Any

from tpy.cache.exceptions import CacheDriverError
from tpy.cache.store import CacheStore


class RedisStore(CacheStore):
    """
    Redis-backed cache.

    Requires ``redis`` (``pip install tamilPY[redis]``).
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        client: Any | None = None,
        prefix: str = "tpy:cache:",
    ) -> None:
        self.prefix = prefix
        if client is not None:
            self.client = client
            return
        try:
            import redis
        except ImportError as error:
            raise CacheDriverError(
                "Redis cache requires the 'redis' package. "
                "Install with: pip install tamilPY[redis]"
            ) from error
        self.client = redis.Redis.from_url(redis_url)

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Any | None:
        raw = self.client.get(self._key(key))
        if raw is None:
            return None
        try:
            return pickle.loads(raw)
        except (pickle.PickleError, TypeError, ValueError):
            self.forget(key)
            return None

    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        namespaced = self._key(key)
        if ttl is None:
            self.client.set(namespaced, payload)
        else:
            self.client.setex(namespaced, int(ttl), payload)

    def forget(self, key: str) -> bool:
        return bool(self.client.delete(self._key(key)))

    def flush(self) -> None:
        pattern = f"{self.prefix}*"
        keys = list(self.client.scan_iter(match=pattern, count=100))
        if keys:
            self.client.delete(*keys)

    def has(self, key: str) -> bool:
        return bool(self.client.exists(self._key(key)))
