"""Tests for Cache Manager stores."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tpy.cache import Cache, CacheDriverError, FileStore, MemoryStore


def test_memory_put_get_forget():
    cache = Cache(MemoryStore())
    cache.put("a", {"x": 1}, ttl=60)
    assert cache.get("a") == {"x": 1}
    assert cache.has("a")
    assert cache.forget("a") is True
    assert cache.get("a", "missing") == "missing"


def test_memory_ttl_expires():
    store = MemoryStore()
    store.put("k", "v", ttl=1)
    assert store.get("k") == "v"
    # Force expiry
    key = "k"
    value, _ = store._data[key]
    store._data[key] = (value, time.time() - 1)
    assert store.get("k") is None


def test_remember_and_pull():
    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return 42

    cache = Cache(MemoryStore())
    assert cache.remember("answer", 60, compute) == 42
    assert cache.remember("answer", 60, compute) == 42
    assert calls["n"] == 1
    assert cache.pull("answer") == 42
    assert cache.get("answer") is None


def test_add_and_increment():
    cache = Cache(MemoryStore())
    assert cache.add("once", "a") is True
    assert cache.add("once", "b") is False
    assert cache.get("once") == "a"
    assert cache.increment("n") == 1
    assert cache.increment("n", 4) == 5
    assert cache.decrement("n", 2) == 3


def test_file_store_roundtrip(tmp_path: Path):
    cache = Cache(FileStore(tmp_path / "cache"))
    cache.put("user:1", {"name": "Ada"}, ttl=120)
    assert cache.get("user:1")["name"] == "Ada"
    cache.flush()
    assert cache.get("user:1") is None


def test_file_store_expires(tmp_path: Path):
    store = FileStore(tmp_path / "cache")
    store.put("x", "y", ttl=1)
    path = store._path("x")
    # Rewrite with past expiry
    import pickle

    path.write_bytes(pickle.dumps(("y", time.time() - 10)))
    assert store.get("x") is None


def test_redis_store_requires_package():
    from tpy.cache.redis_store import RedisStore

    try:
        import redis  # noqa: F401
    except ImportError:
        with pytest.raises(CacheDriverError, match="tamilPY\\[redis\\]"):
            RedisStore()
