from pathlib import Path

from tpy.config.loader import ConfigLoader, Settings
from tpy.providers.base import BaseProvider
from tpy.providers.mongodb.provider import MongoProvider
from tpy.providers.mysql.provider import MySQLProvider
from tpy.providers.postgres.provider import PostgresProvider
from tpy.providers.sqlite.provider import SQLiteProvider


PROVIDERS: dict[str, type[BaseProvider]] = {
    "sqlite": SQLiteProvider,
    "postgres": PostgresProvider,
    "postgresql": PostgresProvider,
    "mysql": MySQLProvider,
    "mongodb": MongoProvider,
    "mongo": MongoProvider,
}


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
    """
    project_root = Path(project_root)
    settings = settings or ConfigLoader(project_root).load()

    provider_name = (name or settings.database or "sqlite").lower()
    provider_cls = PROVIDERS.get(provider_name)

    if provider_cls is None:
        raise ValueError(f"Unknown database provider: {provider_name}")

    url = database_url or settings.database_url
    if provider_name == "sqlite" and not url:
        url = f"sqlite:///{project_root / 'database' / 'database.sqlite3'}"

    return provider_cls(
        database_url=url,
        project_root=project_root,
    )
