from pathlib import Path

import typer

from tpy.database.seeder import SeedRunner
from tpy.providers.factory import get_provider
from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the seed command."""

    @app.command("seed")
    def seed() -> None:
        """
        Run database seed scripts from ``database/seeds``.
        """
        root = Path(".")
        seeds_dir = root / "database" / "seeds"

        if not seeds_dir.exists():
            Console.error(
                "database/seeds not found. Run tpy build inside a TPY project."
            )
            raise typer.Exit(1)

        try:
            Console.info("Seeding database...")
            provider = get_provider(project_root=root)
            runner = SeedRunner(db=provider, project_root=root)
            ran = runner.run()
            provider.close()

            if not ran:
                Console.warning("No seed files found in database/seeds.")
                return

            for name in ran:
                Console.success(f"Seeded: {name}")

            bootstrap = root / "storage" / "auth_bootstrap.txt"
            if bootstrap.exists():
                Console.info(f"Auth bootstrap credentials: {bootstrap}")

            Console.success("Database seeding completed.")
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1)
