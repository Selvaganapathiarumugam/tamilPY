import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


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
        "enum": "TEXT",
    }

    def __init__(
        self,
        database_url: str | None = None,
        project_root: Path | str = ".",
    ) -> None:
        self.database_url = database_url
        self.project_root = Path(project_root)
        self.connection: Any = None

    def __enter__(self) -> "BaseProvider":
        """Connect and return ``self`` for ``with`` usage."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Close the connection when leaving a ``with`` block."""
        self.close()

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

    def ensure_database(self) -> None:
        """
        Create the target database when missing.

        No-op by default. Server providers (Postgres / MySQL) override this.
        """
        return None

    def migrate(self) -> list[str]:
        """
        Run pending migrations from ``database/migrations``.

        Returns:
            List of applied migration module names.
        """
        self.ensure_database()
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

    def quote_identifier(self, name: str) -> str:
        """
        Quote a SQL identifier for reserved words (e.g. ``user``).

        Default dialect uses ANSI double quotes (Postgres / SQLite).
        """
        escaped = str(name).replace('"', '""')
        return f'"{escaped}"'

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
        index_columns: list[str] = []
        table_constraints: list[str] = []

        def flush_create() -> None:
            nonlocal current_table, columns, index_columns, table_constraints
            if current_table is None:
                return
            parts = list(columns) + list(table_constraints)
            body = ", ".join(parts) if parts else ""
            table = self.quote_identifier(current_table)
            statements.append(
                f"CREATE TABLE IF NOT EXISTS {table} ({body})"
            )
            for column_name in index_columns:
                statements.append(
                    self.compile_index(current_table, column_name)
                )
            current_table = None
            columns = []
            index_columns = []
            table_constraints = []

        for operation in operations:
            action = operation["action"]

            if action == "create_table":
                flush_create()
                current_table = operation["table"]
                columns = []
                index_columns = []
                table_constraints = []
                continue

            if action == "column":
                column = operation["column"]
                column_sql = self.compile_column(column)
                if current_table is None:
                    statements.append(column_sql)
                else:
                    columns.append(column_sql)
                    if column.options.get("index") and not column.options.get(
                        "primary"
                    ):
                        index_columns.append(column.name)
                continue

            if action == "unique":
                cols = operation.get("columns") or []
                quoted = ", ".join(self.quote_identifier(c) for c in cols)
                table_constraints.append(f"UNIQUE ({quoted})")
                continue

            if action == "drop_table":
                flush_create()
                table = self.quote_identifier(operation["table"])
                statements.append(f"DROP TABLE IF EXISTS {table}")

        flush_create()
        return statements

    def compile_index(self, table: str, column: str) -> str:
        """
        Build a ``CREATE INDEX`` statement for a single column.

        Args:
            table: Table name.
            column: Column to index.
        """
        index_name = f"idx_{table}_{column}"
        return (
            f"CREATE INDEX IF NOT EXISTS "
            f"{self.quote_identifier(index_name)} "
            f"ON {self.quote_identifier(table)} "
            f"({self.quote_identifier(column)})"
        )

    def compile_column(self, column) -> str:
        """Compile a ``Column`` object into a SQL fragment."""
        datatype = column.datatype
        if str(datatype).startswith("enum"):
            datatype = "enum"
        sql_type = self.TYPE_MAP.get(datatype, "TEXT")
        parts = [self.quote_identifier(column.name), sql_type]
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

        reference = options.get("references")
        if reference:
            ref_table = self.quote_identifier(reference["table"])
            ref_column = self.quote_identifier(reference["column"])
            fk = f"REFERENCES {ref_table} ({ref_column})"
            on_delete = reference.get("on_delete")
            on_update = reference.get("on_update")
            if on_delete:
                fk += f" ON DELETE {self._fk_action_sql(on_delete)}"
            if on_update:
                fk += f" ON UPDATE {self._fk_action_sql(on_update)}"
            parts.append(fk)

        check = options.get("check")
        if check:
            parts.append(f"CHECK ({check})")

        return " ".join(parts)

    def _fk_action_sql(self, action: str) -> str:
        mapping = {
            "cascade": "CASCADE",
            "set_null": "SET NULL",
            "restrict": "RESTRICT",
            "no_action": "NO ACTION",
        }
        return mapping.get(action, "NO ACTION")

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
