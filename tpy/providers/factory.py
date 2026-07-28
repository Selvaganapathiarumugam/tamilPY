from pathlib import Path

from tpy.config.loader import ConfigLoader, Settings
from tpy.providers.base import BaseProvider


_EXTRA_HINTS = {
    "postgres": 'pip install "tamilPY[postgres]"',
    "postgresql": 'pip install "tamilPY[postgres]"',
    "mysql": 'pip install "tamilPY[mysql]"',
    "mongodb": 'pip install "tamilPY[mongodb]"',
    "mongo": 'pip install "tamilPY[mongodb]"',
}


def _load_provider_class(provider_name: str) -> type[BaseProvider]:
    """Lazy-import the concrete provider class."""
    try:
        if provider_name == "sqlite":
            from tpy.providers.sqlite.provider import SQLiteProvider

            return SQLiteProvider
        if provider_name in {"postgres", "postgresql"}:
            from tpy.providers.postgres.provider import PostgresProvider

            return PostgresProvider
        if provider_name == "mysql":
            from tpy.providers.mysql.provider import MySQLProvider

            return MySQLProvider
        if provider_name in {"mongodb", "mongo"}:
            from tpy.providers.mongodb.provider import MongoProvider

            return MongoProvider
    except ImportError as error:
        hint = _EXTRA_HINTS.get(provider_name, 'pip install "tamilPY[all]"')
        raise ImportError(
            f"Database driver for '{provider_name}' is not installed. "
            f"Install with: {hint}"
        ) from error

    raise ValueError(f"Unknown database provider: {provider_name}")


def get_provider(
    name: str | None = None,
    database_url: str | None = None,
    project_root: Path | str = ".",
    settings: Settings | None = None,
) -> BaseProvider:
    """
    Resolve and instantiate a database provider.

    Args:
        name: Provider name override.
        database_url: Connection URL override.
        project_root: Project root path.
        settings: Optional preloaded settings.

    Returns:
        Concrete ``BaseProvider`` instance.

    Raises:
        ValueError: When the provider name is unknown.
        ImportError: When optional driver extras are missing.
    """
    project_root = Path(project_root)
    settings = settings or ConfigLoader(project_root).load()

    provider_name = (name or settings.database or "sqlite").lower()
    provider_cls = _load_provider_class(provider_name)

    url = database_url or settings.database_url
    if provider_name == "sqlite" and not url:
        url = f"sqlite:///{project_root / 'database' / 'database.sqlite3'}"

    return provider_cls(
        database_url=url,
        project_root=project_root,
    )
