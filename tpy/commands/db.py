from pathlib import Path

import typer

from tpy.config.loader import ConfigLoader
from tpy.providers.factory import get_provider
from tpy.utils.console import Console
from tpy.utils.db_wizard import DatabaseWizard


def register(app: typer.Typer) -> None:
    """Register database utility commands."""

    db_app = typer.Typer(help="Database utilities.")
    app.add_typer(db_app, name="db")

    @db_app.command("configure")
    def db_configure() -> None:
        """Interactively choose and configure the database provider."""
        try:
            DatabaseWizard(Path(".")).run()
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1) from error

    @db_app.command("info")
    def db_info() -> None:
        """Show configured database provider details."""
        settings = ConfigLoader(Path(".")).load()
        Console.info(f"Provider : {settings.database}")
        Console.info(f"URL      : {settings.database_url or '(default)'}")

    @db_app.command("ping")
    def db_ping() -> None:
        """Test the database connection."""
        try:
            provider = get_provider(project_root=Path("."))
            provider.connect()
            provider.close()
            Console.success("Database connection OK.")
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1) from error
