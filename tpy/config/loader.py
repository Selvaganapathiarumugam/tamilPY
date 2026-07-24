from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import tomllib


@dataclass
class Settings:
    """
    Application settings loaded from ``tpy.toml`` and environment variables.
    """

    name: str = "tpy-app"
    version: str = "0.1.0"
    backend: str = "fastapi"
    database: str = "sqlite"
    python: str = "3.12"
    database_url: str | None = None
    host: str = "127.0.0.1"
    port: int = 8000
    extra: dict = field(default_factory=dict)


class ConfigLoader:
    """
    Load framework configuration from ``tpy.toml`` and ``.env``.
    """

    def __init__(self, project_root: Path | str = ".") -> None:
        """
        Args:
            project_root: Root directory of the target TPY project.
        """
        self.project_root = Path(project_root)

    def load(self) -> Settings:
        """
        Load and merge configuration sources.

        Returns:
            Populated ``Settings`` instance.
        """
        settings = Settings()
        self._load_toml(settings)
        self._load_env_file()
        self._apply_environment(settings)
        return settings

    def _load_toml(self, settings: Settings) -> None:
        path = self.project_root / "tpy.toml"
        if not path.exists():
            return

        with path.open("rb") as handle:
            data = tomllib.load(handle)

        settings.name = data.get("name", settings.name)
        settings.version = data.get("version", settings.version)
        settings.backend = data.get("backend", settings.backend)
        settings.database = data.get("database", settings.database)
        settings.python = str(data.get("python", settings.python))
        settings.extra = {
            key: value
            for key, value in data.items()
            if key
            not in {
                "name",
                "version",
                "backend",
                "database",
                "python",
            }
        }

    def _load_env_file(self) -> None:
        path = self.project_root / ".env"
        if not path.exists():
            return

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)

    def _apply_environment(self, settings: Settings) -> None:
        settings.database = os.getenv(
            "TPY_DATABASE",
            settings.database,
        )
        settings.database_url = os.getenv(
            "DATABASE_URL",
            settings.database_url,
        )
        settings.host = os.getenv("TPY_HOST", settings.host)
        settings.port = int(os.getenv("TPY_PORT", settings.port))
