from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
import importlib.util


class BaseProvider(ABC):
    """
    Abstract database provider.

    Responsible for connections, SQL execution, and migration workflows.
    """

    PLACEHOLDER = "?"

    TYPE_MAP: dict[str, str] = {
        "string": "TEXT",
        "int": "INTEGER",
        "integer": "INTEGER",
        "float": "REAL",
        "bool": "BOOLEAN",
        "boolean": "BOOLEAN",
        "uuid": "TEXT",
        "datetime": "TIMESTAMP",
    }

    def __init__(
        self,
        database_url: str | None = None,
        project_root: Path | str = ".",
    ) -> None:
        self.database_url = database_url
        self.project_root = Path(project_root)
        self.connection: Any = None

    @abstractmethod
    def connect(self) -> Any:
        """Establish a database connection."""

    def close(self) -> None:
        """Close the active connection when present."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    @abstractmethod
    def execute(self, sql: str, params: tuple | list | None = None) -> Any:
        """Execute a write statement."""

    @abstractmethod
    def fetch_all(self, sql: str, params: tuple | list | None = None) -> list[dict]:
        """Execute a query and return all rows as dictionaries."""

    @abstractmethod
    def fetch_one(self, sql: str, params: tuple | list | None = None) -> dict | None:
        """Execute a query and return one row as a dictionary."""

    def migrate(self) -> list[str]:
        """
        Run pending migrations from ``database/migrations``.

        Returns:
            List of applied migration module names.
        """
        self.connect()
        self.ensure_migrations_table()

        applied: list[str] = []
        for path in self.migration_files():
            name = path.stem
            if self.is_applied(name):
                continue

            migration = self.load_migration(path)
            migration.up()
            statements = self.compile_operations(migration.operations)
            for sql in statements:
                self.execute(sql)
            self.record_migration(name)
            applied.append(name)

        return applied

    def rollback(self) -> str | None:
        """
        Roll back the latest applied migration.

        Returns:
            Rolled-back migration name, or ``None`` when nothing to roll back.
        """
        self.connect()
        self.ensure_migrations_table()

        latest = self.latest_migration()
        if latest is None:
            return None

        path = self.migrations_path / f"{latest}.py"
        if not path.exists():
            return None

        migration = self.load_migration(path)
        migration.down()
        statements = self.compile_operations(migration.operations)
        for sql in statements:
            self.execute(sql)

        self.remove_migration(latest)
        return latest

    @property
    def migrations_path(self) -> Path:
        """Directory containing generated migration modules."""
        return self.project_root / "database" / "migrations"

    def migration_files(self) -> list[Path]:
        """Return sorted migration Python files."""
        if not self.migrations_path.exists():
            return []
        return sorted(self.migrations_path.glob("*_migration.py"))

    def ensure_migrations_table(self) -> None:
        """Create the migrations tracking table if needed."""
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS _tpy_migrations (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def is_applied(self, name: str) -> bool:
        """Return whether a migration name is already recorded."""
        row = self.fetch_one(
            "SELECT name FROM _tpy_migrations WHERE name = ?",
            (name,),
        )
        return row is not None

    def record_migration(self, name: str) -> None:
        """Record a successful migration."""
        self.execute(
            "INSERT INTO _tpy_migrations (name) VALUES (?)",
            (name,),
        )

    def remove_migration(self, name: str) -> None:
        """Remove a migration record after rollback."""
        self.execute(
            "DELETE FROM _tpy_migrations WHERE name = ?",
            (name,),
        )

    def latest_migration(self) -> str | None:
        """Return the most recently applied migration name."""
        row = self.fetch_one(
            """
            SELECT name FROM _tpy_migrations
            ORDER BY id DESC
            LIMIT 1
            """
        )
        if row is None:
            return None
        return row["name"]

    def load_migration(self, path: Path):
        """
        Dynamically import a migration module and instantiate its class.

        Args:
            path: Path to a ``*_migration.py`` file.
        """
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load migration: {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attribute in vars(module).values():
            if (
                isinstance(attribute, type)
                and attribute.__name__.endswith("Migration")
                and attribute.__name__ != "Migration"
            ):
                return attribute()

        raise ImportError(f"No Migration class found in {path}")

    def compile_operations(self, operations: list[dict]) -> list[str]:
        """
        Compile migration operations into SQL statements.

        Args:
            operations: Operations collected by a ``Migration`` instance.

        Returns:
            Ordered SQL statements.
        """
        statements: list[str] = []
        current_table: str | None = None
        columns: list[str] = []

        def flush_create() -> None:
            nonlocal current_table, columns
            if current_table is None:
                return
            body = ", ".join(columns) if columns else ""
            statements.append(
                f"CREATE TABLE IF NOT EXISTS {current_table} ({body})"
            )
            current_table = None
            columns = []

        for operation in operations:
            action = operation["action"]

            if action == "create_table":
                flush_create()
                current_table = operation["table"]
                columns = []
                continue

            if action == "column":
                column_sql = self.compile_column(operation["column"])
                if current_table is None:
                    statements.append(column_sql)
                else:
                    columns.append(column_sql)
                continue

            if action == "drop_table":
                flush_create()
                statements.append(
                    f"DROP TABLE IF EXISTS {operation['table']}"
                )

        flush_create()
        return statements

    def compile_column(self, column) -> str:
        """Compile a ``Column`` object into a SQL fragment."""
        sql_type = self.TYPE_MAP.get(column.datatype, "TEXT")
        parts = [column.name, sql_type]
        options = column.options

        if options.get("primary"):
            parts.append("PRIMARY KEY")
        if options.get("unique"):
            parts.append("UNIQUE")
        if options.get("nullable"):
            parts.append("NULL")
        elif not options.get("primary"):
            parts.append("NOT NULL")
        if "default" in options:
            parts.append(f"DEFAULT {self.format_default(options['default'])}")

        return " ".join(parts)

    def format_default(self, value: Any) -> str:
        """Format a default value for SQL."""
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        if value is None:
            return "NULL"
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"

    def bind_parameters(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> tuple[str, dict | tuple | list]:
        """
        Adapt ``?`` placeholders for the active provider dialect.

        Returns:
            Tuple of SQL string and parameter payload.
        """
        if self.PLACEHOLDER == "?" or not params:
            return sql, params or ()

        values = list(params)
        rendered: list[str] = []
        mapping: dict[str, Any] = {}
        index = 0

        for char in sql:
            if char == "?":
                key = f"p{index}"
                rendered.append(f":{key}")
                mapping[key] = values[index]
                index += 1
            else:
                rendered.append(char)

        return "".join(rendered), mapping
