"""
tamilPY Cache Manager.
"""

from tpy.cache.exceptions import CacheDriverError, CacheError
from tpy.cache.file import FileStore
from tpy.cache.manager import Cache
from tpy.cache.memory import MemoryStore
from tpy.cache.store import CacheStore

__all__ = [
    "Cache",
    "CacheDriverError",
    "CacheError",
    "CacheStore",
    "FileStore",
    "MemoryStore",
]


def __getattr__(name: str):
    if name == "RedisStore":
        from tpy.cache.redis_store import RedisStore

        return RedisStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
