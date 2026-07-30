from pathlib import Path

import typer

from tpy.providers.factory import get_provider
from tpy.runtime.builder import Builder
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
            raise typer.Exit(1) from error

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
            raise typer.Exit(1) from error


def _missing_migration_models(project_root: Path) -> list[str]:
    """
    Return schema model names that have no ``*_model_migration.py`` file yet.
    """
    schema_path = project_root / "schema.tpy"
    if not schema_path.exists():
        return []

    try:
        ast = Builder(project_root).parse_schema()
    except Exception:
        return []

    migrations_dir = project_root / "database" / "migrations"
    missing: list[str] = []
    for model in ast.models:
        stem = model.name.lower()
        if not list(migrations_dir.glob(f"*_{stem}_migration.py")):
            missing.append(model.name)
    return missing


def _ensure_migrations_from_schema(project_root: Path) -> None:
    """
    Generate CRUD / migration files when ``schema.tpy`` has new models.

    Lets users run ``tpy migrate`` after editing the schema without a
    separate ``tpy crud`` step.
    """
    missing = _missing_migration_models(project_root)
    if not missing:
        return

    names = ", ".join(missing)
    Console.info(
        f"New model(s) in schema.tpy without migrations: {names}."
    )
    Console.info("Generating CRUD + migration files...")
    ast = Builder(project_root).build()
    Console.success(
        f"Generated layers for {len(ast.models)} model(s)."
    )
    Console.info(
        "Tip: run `tpy admin` to refresh the React dashboard."
    )


def _run_migrate() -> None:
    try:
        root = Path(".")
        _ensure_migrations_from_schema(root)

        provider = get_provider(project_root=root)
        Console.info("Ensuring database exists...")
        provider.ensure_database()
        Console.info("Running migrations...")
        applied = provider.migrate()
        provider.close()

        if not applied:
            Console.info("Nothing to migrate.")
            return

        for name in applied:
            Console.success(f"Migrated: {name}")
    except Exception as error:
        Console.error(str(error))
        raise typer.Exit(1) from error
