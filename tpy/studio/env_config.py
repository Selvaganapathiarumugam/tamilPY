"""Read/write project ``.env`` for Studio database panel (secrets redacted)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

_SECRET_KEYS = frozenset(
    {
        "DATABASE_URL",
        "PASSWORD",
        "DB_PASSWORD",
        "SECRET_KEY",
        "JWT_SECRET",
        "WEBHOOK_SECRET",
    }
)


def read_env(project_root: Path) -> dict[str, str]:
    """Parse ``.env`` into a flat dict."""
    path = Path(project_root) / ".env"
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def write_env(project_root: Path, updates: dict[str, str]) -> None:
    """Merge ``updates`` into ``.env``, preserving unrelated keys."""
    path = Path(project_root) / ".env"
    existing = read_env(project_root)
    existing.update({k: str(v) for k, v in updates.items() if v is not None})
    lines = [f"{key}={value}" for key, value in existing.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def redact_value(key: str, value: str) -> str:
    """Mask secrets for API responses."""
    upper = key.upper()
    if upper in _SECRET_KEYS or "PASSWORD" in upper or "SECRET" in upper:
        if not value:
            return ""
        return "****"
    if upper == "DATABASE_URL" or "URL" in upper:
        return redact_url(value)
    return value


def redact_url(url: str) -> str:
    """Mask password segment inside a database URL."""
    if not url or "://" not in url:
        return url
    try:
        # Handle sqlalchemy-style schemes
        normalized = url.replace("postgresql+psycopg2://", "postgresql://", 1)
        normalized = normalized.replace("mysql+pymysql://", "mysql://", 1)
        parsed = urlparse(normalized)
        if parsed.password is None:
            return url
        user = parsed.username or ""
        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        netloc = f"{user}:****@{host}{port}"
        redacted = urlunparse(
            (parsed.scheme, netloc, parsed.path, "", parsed.query, "")
        )
        if url.startswith("postgresql+psycopg2://"):
            return redacted.replace("postgresql://", "postgresql+psycopg2://", 1)
        if url.startswith("mysql+pymysql://"):
            return redacted.replace("mysql://", "mysql+pymysql://", 1)
        return redacted
    except Exception:
        return re.sub(r":([^:@/]+)@", ":****@", url)


def database_public_config(project_root: Path) -> dict[str, Any]:
    """Return DB settings safe for the Studio frontend."""
    env = read_env(project_root)
    provider = env.get("TPY_DATABASE", "sqlite")
    return {
        "provider": provider,
        "database_url": redact_value("DATABASE_URL", env.get("DATABASE_URL", "")),
        "host": env.get("DB_HOST") or env.get("TPY_DB_HOST", ""),
        "port": env.get("DB_PORT", ""),
        "database_name": env.get("DB_NAME", ""),
        "username": env.get("DB_USER", ""),
        "password_set": bool(
            env.get("DB_PASSWORD")
            or (
                env.get("DATABASE_URL")
                and "@" in env.get("DATABASE_URL", "")
                and ":@" not in env.get("DATABASE_URL", "")
            )
        ),
        "env": {
            key: redact_value(key, value) for key, value in sorted(env.items())
        },
    }


def build_database_url(payload: dict[str, Any]) -> tuple[str, str]:
    """
    Build ``(provider, database_url)`` from Studio database form payload.
    """
    provider = str(payload.get("provider") or "sqlite").lower()
    if provider == "sqlite":
        default_db = "database/database.sqlite3"
        path = str(payload.get("database_url") or payload.get("path") or default_db)
        if path.startswith("sqlite:///"):
            return provider, path
        return provider, f"sqlite:///{path}"

    host = str(payload.get("host") or "127.0.0.1")
    database = str(payload.get("database_name") or "tpy")
    username = str(payload.get("username") or "")
    password = str(payload.get("password") or "")
    if provider == "postgres":
        port = str(payload.get("port") or "5432")
        url = (
            f"postgresql+psycopg2://{username}:{password}"
            f"@{host}:{port}/{database}"
        )
        return provider, url
    if provider == "mysql":
        port = str(payload.get("port") or "3306")
        url = (
            f"mysql+pymysql://{username}:{password}"
            f"@{host}:{port}/{database}"
        )
        return provider, url
    if provider == "mongodb":
        port = str(payload.get("port") or "27017")
        if username:
            url = f"mongodb://{username}:{password}@{host}:{port}/{database}"
        else:
            url = f"mongodb://{host}:{port}/{database}"
        return provider, url
    raise ValueError(f"Unsupported provider '{provider}'")
