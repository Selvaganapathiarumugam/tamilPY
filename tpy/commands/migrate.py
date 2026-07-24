from pathlib import Path

import typer

from tpy.providers.factory import get_provider
from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register migration commands."""

    migrate_app = typer.Typer(help="Database migration commands.")
    app.add_typer(migrate_app, name="migrate")

    @migrate_app.callback(invoke_without_command=True)
    def migrate_default(
        ctx: typer.Context,
    ) -> None:
        """Run pending migrations when no subcommand is given."""
        if ctx.invoked_subcommand is not None:
            return
        _run_migrate()

    @migrate_app.command("up")
    def migrate_up() -> None:
        """Apply pending migrations."""
        _run_migrate()

    @migrate_app.command("rollback")
    def migrate_rollback() -> None:
        """Roll back the latest migration."""
        try:
            provider = get_provider(project_root=Path("."))
            name = provider.rollback()
            provider.close()

            if name is None:
                Console.warning("No migrations to roll back.")
                return

            Console.success(f"Rolled back: {name}")
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1)

    @migrate_app.command("status")
    def migrate_status() -> None:
        """Show applied migrations."""
        try:
            provider = get_provider(project_root=Path("."))
            provider.connect()
            provider.ensure_migrations_table()
            rows = provider.fetch_all(
                "SELECT name, applied_at FROM _tpy_migrations ORDER BY id"
            )
            provider.close()

            if not rows:
                Console.info("No migrations applied yet.")
                return

            for row in rows:
                Console.info(f"{row['name']} @ {row['applied_at']}")
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1)


def _run_migrate() -> None:
    try:
        Console.info("Running migrations...")
        provider = get_provider(project_root=Path("."))
        applied = provider.migrate()
        provider.close()

        if not applied:
            Console.info("Nothing to migrate.")
            return

        for name in applied:
            Console.success(f"Migrated: {name}")
    except Exception as error:
        Console.error(str(error))
        raise typer.Exit(1)
