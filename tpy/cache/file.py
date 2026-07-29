"""
File-backed cache store.
"""

from __future__ import annotations

import hashlib
import pickle
import time
from pathlib import Path
from typing import Any

from tpy.cache.store import CacheStore


class FileStore(CacheStore):
    """
    Filesystem cache under a directory.

    Each key maps to a pickled file containing ``(value, expires_at|None)``.
    """

    def __init__(self, directory: Path | str = "storage/framework/cache") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.directory / f"{digest}.cache"

    def get(self, key: str) -> Any | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            value, expires = pickle.loads(path.read_bytes())
        except (OSError, pickle.PickleError, ValueError, TypeError):
            path.unlink(missing_ok=True)
            return None
        if expires is not None and time.time() >= expires:
            path.unlink(missing_ok=True)
            return None
        return value

    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires = None if ttl is None else time.time() + ttl
        path = self._path(key)
        path.write_bytes(pickle.dumps((value, expires), protocol=pickle.HIGHEST_PROTOCOL))

    def forget(self, key: str) -> bool:
        path = self._path(key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def flush(self) -> None:
        for path in self.directory.glob("*.cache"):
            path.unlink(missing_ok=True)

    def has(self, key: str) -> bool:
        return self.get(key) is not None
