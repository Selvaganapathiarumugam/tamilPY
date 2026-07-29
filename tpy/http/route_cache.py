"""
Cache FastAPI route metadata for inspection and faster tooling.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RouteCache:
    """
    Persist a snapshot of application routes.

    This does not replace FastAPI routing at runtime; it caches route
    metadata (path, methods, name, endpoint) for CLI/doctor/boot tooling.
    """

    def __init__(self, base_path: Path | str = ".") -> None:
        self.base_path = Path(base_path)
        self.cache_file = (
            self.base_path / "storage" / "framework" / "routes.cache.json"
        )

    def path(self) -> Path:
        """Return the cache file path."""
        return self.cache_file

    def dump(self, app: Any) -> Path:
        """
        Serialize routes from a FastAPI/Starlette ``app`` to disk.
        """
        routes = self.collect(app)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "routes": routes}
        self.cache_file.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        return self.cache_file

    def load(self) -> list[dict[str, Any]]:
        """Load cached routes (empty list when missing)."""
        if not self.cache_file.exists():
            return []
        data = json.loads(self.cache_file.read_text(encoding="utf-8"))
        return list(data.get("routes", []))

    def clear(self) -> bool:
        """Delete the route cache file."""
        if self.cache_file.exists():
            self.cache_file.unlink()
            return True
        return False

    def exists(self) -> bool:
        """Return whether a cache file is present."""
        return self.cache_file.exists()

    @staticmethod
    def collect(app: Any) -> list[dict[str, Any]]:
        """Collect route metadata from ``app.routes``."""
        collected: list[dict[str, Any]] = []
        for route in getattr(app, "routes", []):
            path = getattr(route, "path", None)
            if path is None:
                continue
            methods = sorted(
                method
                for method in (getattr(route, "methods", None) or [])
                if method not in {"HEAD", "OPTIONS"}
            )
            endpoint = getattr(route, "endpoint", None)
            name = getattr(route, "name", None) or getattr(
                endpoint, "__name__", None
            )
            endpoint_path = None
            if endpoint is not None:
                module = getattr(endpoint, "__module__", None)
                qual = getattr(endpoint, "__qualname__", None)
                if module and qual:
                    endpoint_path = f"{module}:{qual}"
            collected.append(
                {
                    "path": path,
                    "methods": methods,
                    "name": name,
                    "endpoint": endpoint_path,
                }
            )
        return collected
