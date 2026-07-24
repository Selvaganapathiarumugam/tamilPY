from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import typer

from tpy.utils.console import Console
from tpy.utils.file_manager import FileManager


@dataclass
class DatabaseChoice:
    """Selected database provider and connection settings."""

    provider: str
    database_url: str
    host: str = "127.0.0.1"
    port: str = ""
    database_name: str = ""
    username: str = ""
    password: str = ""
    extra: dict[str, str] | None = None


class DatabaseWizard:
    """
    Interactive console wizard for choosing and configuring a database.

    Writes ``.env``, updates ``tpy.toml``, and syncs ``schema.tpy``.
    """

    OPTIONS: list[tuple[str, str, str]] = [
        ("1", "sqlite", "SQLite (local file, zero setup)"),
        ("2", "postgres", "PostgreSQL"),
        ("3", "mysql", "MySQL"),
        ("4", "mongodb", "MongoDB"),
    ]

    def __init__(self, project_root: Path | str = ".") -> None:
        self.project_root = Path(project_root)

    def run(self) -> DatabaseChoice:
        """
        Prompt the user for provider and connection details.

        Returns:
            Fully populated ``DatabaseChoice``.
        """
        Console.info("")
        Console.info("Select database provider for your app:")
        Console.info("")

        for key, _, label in self.OPTIONS:
            Console.info(f"  {key}) {label}")

        Console.info("")
        selection = typer.prompt("Enter option number", default="1").strip()

        provider = self._resolve_provider(selection)
        Console.success(f"Selected: {provider}")
        Console.info("")

        if provider == "sqlite":
            choice = self._ask_sqlite()
        elif provider == "postgres":
            choice = self._ask_postgres()
        elif provider == "mysql":
            choice = self._ask_mysql()
        else:
            choice = self._ask_mongodb()

        self.apply(choice)
        return choice

    def apply(self, choice: DatabaseChoice) -> None:
        """Persist database settings into project config files."""
        self._write_env(choice)
        self._update_toml(choice.provider)
        self._update_schema(choice.provider)
        Console.success("Database configuration saved to .env and tpy.toml")

    def _resolve_provider(self, selection: str) -> str:
        for key, provider, _ in self.OPTIONS:
            if selection == key or selection.lower() == provider:
                return provider

        Console.warning("Invalid option. Falling back to SQLite.")
        return "sqlite"

    def _ask_sqlite(self) -> DatabaseChoice:
        path = typer.prompt(
            "SQLite file path",
            default="database/database.sqlite3",
        ).strip()
        url = path if path.startswith("sqlite:///") else f"sqlite:///{path}"
        return DatabaseChoice(provider="sqlite", database_url=url)

    def _ask_postgres(self) -> DatabaseChoice:
        host = typer.prompt("Host", default="127.0.0.1").strip()
        port = typer.prompt("Port", default="5432").strip()
        database = typer.prompt("Database name").strip()
        username = typer.prompt("Username", default="postgres").strip()
        password = typer.prompt("Password", hide_input=True).strip()
        url = (
            f"postgresql+psycopg2://{username}:{password}"
            f"@{host}:{port}/{database}"
        )
        return DatabaseChoice(
            provider="postgres",
            database_url=url,
            host=host,
            port=port,
            database_name=database,
            username=username,
            password=password,
        )

    def _ask_mysql(self) -> DatabaseChoice:
        host = typer.prompt("Host", default="127.0.0.1").strip()
        port = typer.prompt("Port", default="3306").strip()
        database = typer.prompt("Database name").strip()
        username = typer.prompt("Username", default="root").strip()
        password = typer.prompt("Password", hide_input=True).strip()
        url = (
            f"mysql+pymysql://{username}:{password}"
            f"@{host}:{port}/{database}"
        )
        return DatabaseChoice(
            provider="mysql",
            database_url=url,
            host=host,
            port=port,
            database_name=database,
            username=username,
            password=password,
        )

    def _ask_mongodb(self) -> DatabaseChoice:
        host = typer.prompt("Host", default="127.0.0.1").strip()
        port = typer.prompt("Port", default="27017").strip()
        database = typer.prompt("Database name", default="tpy").strip()
        username = typer.prompt(
            "Username (leave empty if none)",
            default="",
        ).strip()
        password = ""
        if username:
            password = typer.prompt("Password", hide_input=True).strip()
            url = (
                f"mongodb://{username}:{password}@{host}:{port}/{database}"
            )
        else:
            url = f"mongodb://{host}:{port}/{database}"

        return DatabaseChoice(
            provider="mongodb",
            database_url=url,
            host=host,
            port=port,
            database_name=database,
            username=username,
            password=password,
        )

    def _write_env(self, choice: DatabaseChoice) -> None:
        env_path = self.project_root / ".env"
        existing: dict[str, str] = {}

        if env_path.exists():
            for raw in env_path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                existing[key.strip()] = value.strip()

        existing["TPY_DATABASE"] = choice.provider
        existing["DATABASE_URL"] = choice.database_url
        existing.setdefault("TPY_HOST", "127.0.0.1")
        existing.setdefault("TPY_PORT", "8000")

        if choice.host and choice.provider != "sqlite":
            existing["DB_HOST"] = choice.host
        if choice.port:
            existing["DB_PORT"] = choice.port
        if choice.database_name:
            existing["DB_NAME"] = choice.database_name
        if choice.username:
            existing["DB_USER"] = choice.username
        if choice.password:
            existing["DB_PASSWORD"] = choice.password

        lines = [
            "# Generated by TPY build — database configuration",
            f"TPY_DATABASE={existing['TPY_DATABASE']}",
            f"DATABASE_URL={existing['DATABASE_URL']}",
            f"TPY_HOST={existing.get('TPY_HOST', '127.0.0.1')}",
            f"TPY_PORT={existing.get('TPY_PORT', '8000')}",
        ]

        for key in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"):
            if key in existing and choice.provider != "sqlite":
                lines.append(f"{key}={existing[key]}")
            elif key in existing and choice.provider == "sqlite":
                # Keep non-DB connection keys only for server-style providers.
                continue

        FileManager.write(env_path, "\n".join(lines) + "\n")

    def _update_toml(self, provider: str) -> None:
        path = self.project_root / "tpy.toml"
        if not path.exists():
            FileManager.write(
                path,
                f'name = "tpy-app"\nversion = "0.1.0"\n'
                f'backend = "fastapi"\ndatabase = "{provider}"\n'
                f'python = "3.12"\n',
            )
            return

        text = path.read_text(encoding="utf-8")
        if re.search(r'^database\s*=', text, flags=re.MULTILINE):
            text = re.sub(
                r'^database\s*=\s*".*"',
                f'database = "{provider}"',
                text,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            text = text.rstrip() + f'\ndatabase = "{provider}"\n'

        FileManager.write(path, text)

    def _update_schema(self, provider: str) -> None:
        path = self.project_root / "schema.tpy"
        if not path.exists():
            return

        text = path.read_text(encoding="utf-8")
        if re.search(r'^database\s+\w+', text, flags=re.MULTILINE):
            text = re.sub(
                r'^database\s+\w+',
                f"database {provider}",
                text,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            text = f"database {provider}\n\n{text.lstrip()}"

        FileManager.write(path, text)
