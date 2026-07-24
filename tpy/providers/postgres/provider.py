from pathlib import Path
from typing import Any

from tpy.providers.base import BaseProvider
from tpy.utils.console import Console


class PostgresProvider(BaseProvider):
    """
    PostgreSQL database provider powered by SQLAlchemy.
    """

    PLACEHOLDER = "%s"

    TYPE_MAP: dict[str, str] = {
        "string": "VARCHAR(255)",
        "int": "INTEGER",
        "integer": "INTEGER",
        "float": "DOUBLE PRECISION",
        "bool": "BOOLEAN",
        "boolean": "BOOLEAN",
        "uuid": "UUID",
        "datetime": "TIMESTAMP",
    }

    def ensure_database(self) -> None:
        """Create the PostgreSQL database when it does not exist."""
        if not self.database_url:
            return

        from sqlalchemy import create_engine, text
        from sqlalchemy.engine.url import make_url

        url = make_url(self.database_url)
        db_name = url.database
        if not db_name:
            return

        last_error: Exception | None = None
        for maintenance_db in ("postgres", "template1"):
            admin_url = url.set(database=maintenance_db)
            engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
            try:
                with engine.connect() as connection:
                    exists = connection.execute(
                        text(
                            "SELECT 1 FROM pg_database WHERE datname = :name"
                        ),
                        {"name": db_name},
                    ).scalar()
                    if exists:
                        return
                    quoted = self.quote_identifier(db_name)
                    connection.execute(text(f"CREATE DATABASE {quoted}"))
                    Console.success(f"Created database: {db_name}")
                    return
            except Exception as error:
                last_error = error
            finally:
                engine.dispose()

        raise RuntimeError(
            f"Could not create database '{db_name}'. "
            "Check Postgres is running and the user can CREATE DATABASE. "
            f"Details: {last_error}"
        )

    def connect(self) -> Any:
        """Create a SQLAlchemy connection."""
        if self.connection is not None:
            return self.connection

        if not self.database_url:
            raise ValueError(
                "DATABASE_URL is required for the postgres provider."
            )

        from sqlalchemy import create_engine

        engine = create_engine(self.database_url)
        self.connection = engine.connect()
        return self.connection

    def close(self) -> None:
        """Close the SQLAlchemy connection."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> Any:
        """Execute a write statement."""
        from sqlalchemy import text

        connection = self.connect()
        query, payload = self.bind_parameters(sql, params)
        result = connection.execute(text(query), payload)
        connection.commit()
        return result

    def fetch_all(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> list[dict]:
        """Return all rows as dictionaries."""
        from sqlalchemy import text

        connection = self.connect()
        query, payload = self.bind_parameters(sql, params)
        result = connection.execute(text(query), payload)
        return [dict(row._mapping) for row in result]

    def fetch_one(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> dict | None:
        """Return one row as a dictionary."""
        from sqlalchemy import text

        connection = self.connect()
        query, payload = self.bind_parameters(sql, params)
        result = connection.execute(text(query), payload)
        row = result.first()
        return dict(row._mapping) if row is not None else None

    def ensure_migrations_table(self) -> None:
        """Create the migrations tracking table for Postgres."""
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS _tpy_migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
