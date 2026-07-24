from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tpy.providers.base import BaseProvider


class SQLiteProvider(BaseProvider):
    """
    SQLite database provider.
    """

    TYPE_MAP: dict[str, str] = {
        "string": "TEXT",
        "int": "INTEGER",
        "integer": "INTEGER",
        "float": "REAL",
        "bool": "INTEGER",
        "boolean": "INTEGER",
        "uuid": "TEXT",
        "datetime": "TEXT",
    }

    def __init__(
        self,
        database_url: str | None = None,
        project_root: Path | str = ".",
    ) -> None:
        super().__init__(database_url, project_root)
        self.db_path = self._resolve_path(database_url)

    def _resolve_path(self, database_url: str | None) -> Path:
        if not database_url:
            return self.project_root / "database" / "database.sqlite3"

        if database_url.startswith("sqlite:///"):
            raw = database_url.removeprefix("sqlite:///")
            path = Path(raw)
            if not path.is_absolute():
                path = self.project_root / path
            return path

        parsed = urlparse(database_url)
        if parsed.scheme in {"", "sqlite"}:
            path = Path(parsed.path or database_url)
            if not path.is_absolute():
                path = self.project_root / path
            return path

        return self.project_root / "database" / "database.sqlite3"

    def connect(self) -> sqlite3.Connection:
        """Open a SQLite connection with Row factory enabled."""
        if self.connection is not None:
            return self.connection

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        self.connection = connection
        return connection

    def execute(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> sqlite3.Cursor:
        """Execute a write statement and commit."""
        connection = self.connect()
        cursor = connection.execute(sql, params or ())
        connection.commit()
        return cursor

    def fetch_all(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> list[dict]:
        """Return all rows as dictionaries."""
        connection = self.connect()
        cursor = connection.execute(sql, params or ())
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> dict | None:
        """Return one row as a dictionary."""
        connection = self.connect()
        cursor = connection.execute(sql, params or ())
        row = cursor.fetchone()
        return dict(row) if row is not None else None
