from pathlib import Path
from typing import Any

from tpy.providers.base import BaseProvider


class MySQLProvider(BaseProvider):
    """
    MySQL database provider powered by SQLAlchemy.
    """

    PLACEHOLDER = "%s"

    TYPE_MAP: dict[str, str] = {
        "string": "VARCHAR(255)",
        "int": "INT",
        "integer": "INT",
        "float": "DOUBLE",
        "bool": "TINYINT(1)",
        "boolean": "TINYINT(1)",
        "uuid": "CHAR(36)",
        "datetime": "DATETIME",
    }

    def quote_identifier(self, name: str) -> str:
        """Quote a MySQL identifier with backticks."""
        escaped = str(name).replace("`", "``")
        return f"`{escaped}`"

    def ensure_database(self) -> None:
        """Create the MySQL database when it does not exist."""
        if not self.database_url:
            return

        from sqlalchemy import create_engine, text
        from sqlalchemy.engine.url import make_url

        from tpy.utils.console import Console

        url = make_url(self.database_url)
        db_name = url.database
        if not db_name:
            return

        # Connect without a default schema so CREATE DATABASE is allowed.
        admin_url = url.set(database=None)
        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        try:
            with engine.connect() as connection:
                quoted = self.quote_identifier(db_name)
                result = connection.execute(
                    text(
                        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                        "WHERE SCHEMA_NAME = :name"
                    ),
                    {"name": db_name},
                ).scalar()
                if result:
                    return
                connection.execute(
                    text(f"CREATE DATABASE {quoted}")
                )
                Console.success(f"Created database: {db_name}")
        except Exception as error:
            raise RuntimeError(
                f"Could not create database '{db_name}'. "
                "Check MySQL is running and the user can CREATE DATABASE. "
                f"Details: {error}"
            ) from error
        finally:
            engine.dispose()

    def connect(self) -> Any:
        """Create a SQLAlchemy connection."""
        if self.connection is not None:
            return self.connection

        if not self.database_url:
            raise ValueError(
                "DATABASE_URL is required for the mysql provider."
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
        """Create the migrations tracking table for MySQL."""
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS _tpy_migrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
