"""
Configuration manager — nested keys, env overlay, optional file cache.
"""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path
from typing import Any

from tpy.config.loader import ConfigLoader, Settings
from tpy.exceptions import TpyConfigError


class Config:
    """
    Nested configuration store with dot-key access.

    Sources (later wins): defaults → ``tpy.toml`` → ``.env`` / process env →
    optional runtime ``set()``.
    """

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        *,
        base_path: Path | str = ".",
        settings: Settings | None = None,
    ) -> None:
        self.base_path = Path(base_path)
        self._data: dict[str, Any] = data or {}
        self.settings = settings or Settings()

    @classmethod
    def load(cls, base_path: Path | str = ".") -> Config:
        """
        Load configuration from ``tpy.toml`` + env via ``ConfigLoader``.
        """
        root = Path(base_path)
        loader = ConfigLoader(root)
        settings = loader.load()
        data = cls._settings_to_dict(settings)
        # Merge full toml tree under keys when present
        toml_path = root / "tpy.toml"
        if toml_path.exists():
            with toml_path.open("rb") as handle:
                raw = tomllib.load(handle)
            data = cls._deep_merge(data, cls._normalize_toml(raw))
        # Re-apply env overrides for nested form
        cls._apply_env_overrides(data)
        return cls(data, base_path=root, settings=settings)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by dotted key (e.g. ``app.name``)."""
        parts = key.split(".")
        current: Any = self._data
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a dotted key at runtime (in-memory)."""
        parts = key.split(".")
        current = self._data
        for part in parts[:-1]:
            nxt = current.setdefault(part, {})
            if not isinstance(nxt, dict):
                raise TpyConfigError(f"Cannot set '{key}': '{part}' is not a map")
            current = nxt
        current[parts[-1]] = value

    def has(self, key: str) -> bool:
        """Return whether a dotted key exists."""
        sentinel = object()
        return self.get(key, sentinel) is not sentinel

    def all(self) -> dict[str, Any]:
        """Return a shallow copy of the root config dict."""
        return dict(self._data)

    def section(self, name: str) -> dict[str, Any]:
        """Return a config section dict (empty if missing)."""
        value = self.get(name, {})
        return dict(value) if isinstance(value, dict) else {}

    def cache_path(self) -> Path:
        """Path used by ``cache()`` / ``load_cached()``."""
        return self.base_path / "storage" / "framework" / "config.cache.json"

    def is_cached(self) -> bool:
        """Return whether a config cache file exists."""
        return self.cache_path().exists()

    def cache_is_fresh(self) -> bool:
        """
        Return True when the cache exists and is newer than ``tpy.toml`` / ``.env``.
        """
        cache = self.cache_path()
        if not cache.exists():
            return False
        cache_mtime = cache.stat().st_mtime
        for name in ("tpy.toml", ".env"):
            source = self.base_path / name
            if source.exists() and source.stat().st_mtime > cache_mtime:
                return False
        return True

    @classmethod
    def prefer_cache_enabled(cls) -> bool:
        """Whether env requests preferring the config cache."""
        flag = os.getenv("TPY_CONFIG_CACHE", "").strip().lower()
        return flag in {"1", "true", "yes", "on"}

    @classmethod
    def load_auto(
        cls,
        base_path: Path | str = ".",
        *,
        prefer_cache: bool | None = None,
    ) -> Config:
        """
        Load config, optionally from cache.

        Uses cache when ``prefer_cache`` is True (or ``TPY_CONFIG_CACHE`` is set)
        and the cache file is fresh.
        """
        root = Path(base_path)
        use_cache = (
            cls.prefer_cache_enabled()
            if prefer_cache is None
            else prefer_cache
        )
        probe = cls(base_path=root)
        if use_cache and probe.cache_is_fresh():
            return cls.load_cached(root)
        return cls.load(root)

    def cache(self) -> Path:
        """
        Persist current config to a JSON cache file.

        Used by ``tpy config cache`` / ``tpy optimize``.
        """
        path = self.cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._data, indent=2, default=str),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load_cached(cls, base_path: Path | str = ".") -> Config:
        """
        Load config from cache file when present; otherwise ``load()``.
        """
        root = Path(base_path)
        path = root / "storage" / "framework" / "config.cache.json"
        if not path.exists():
            return cls.load(root)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise TpyConfigError(f"Invalid config cache: {error}") from error
        settings = Settings(
            name=str(data.get("app", {}).get("name", "tpy-app")),
            version=str(data.get("app", {}).get("version", "0.1.0")),
            backend=str(data.get("app", {}).get("backend", "fastapi")),
            database=str(data.get("database", {}).get("driver", "sqlite")),
            database_url=data.get("database", {}).get("url"),
            host=str(data.get("server", {}).get("host", "127.0.0.1")),
            port=int(data.get("server", {}).get("port", 8000)),
        )
        return cls(data, base_path=root, settings=settings)

    def clear_cache(self) -> bool:
        """Delete the config cache file. Return whether it existed."""
        path = self.cache_path()
        if path.exists():
            path.unlink()
            return True
        return False

    @staticmethod
    def _settings_to_dict(settings: Settings) -> dict[str, Any]:
        return {
            "app": {
                "name": settings.name,
                "version": settings.version,
                "backend": settings.backend,
                "python": settings.python,
            },
            "database": {
                "driver": settings.database,
                "url": settings.database_url,
            },
            "server": {
                "host": settings.host,
                "port": settings.port,
            },
            "extra": dict(settings.extra),
        }

    @staticmethod
    def _normalize_toml(raw: dict[str, Any]) -> dict[str, Any]:
        known = {"name", "version", "backend", "database", "python"}
        nested = {
            "app": {
                key: raw[key]
                for key in ("name", "version", "backend", "python")
                if key in raw
            },
            "database": {},
            "server": {},
            "extra": {},
        }
        if "database" in raw and not isinstance(raw["database"], dict):
            nested["database"]["driver"] = raw["database"]
        for key, value in raw.items():
            if key in known:
                continue
            if isinstance(value, dict):
                nested[key] = value
            else:
                nested["extra"][key] = value
        return nested

    @staticmethod
    def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
        result = dict(base)
        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = Config._deep_merge(result[key], value)
            elif value not in (None, {}):
                result[key] = value
        return result

    @staticmethod
    def _apply_env_overrides(data: dict[str, Any]) -> None:
        app = data.setdefault("app", {})
        database = data.setdefault("database", {})
        server = data.setdefault("server", {})
        if os.getenv("TPY_DATABASE"):
            database["driver"] = os.environ["TPY_DATABASE"]
        if os.getenv("DATABASE_URL"):
            database["url"] = os.environ["DATABASE_URL"]
        if os.getenv("TPY_HOST"):
            server["host"] = os.environ["TPY_HOST"]
        if os.getenv("TPY_PORT"):
            server["port"] = int(os.environ["TPY_PORT"])
        if os.getenv("TPY_APP_NAME"):
            app["name"] = os.environ["TPY_APP_NAME"]
