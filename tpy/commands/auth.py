from pathlib import Path

import typer

from tpy.generator.auth_generator import AuthGenerator
from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the auth generation command."""

    @app.command("auth")
    def auth() -> None:
        """
        Generate JWT auth (login/register/refresh/logout), AuthRole + User,
        and default role seed data.
        """
        root = Path(".")
        if not (root / "schema.tpy").exists():
            Console.error("schema.tpy not found. Run this inside a TPY project.")
            raise typer.Exit(1)

        try:
            Console.info("Generating JWT auth...")
            model_count = AuthGenerator(root).generate()
            Console.success(
                f"Auth enabled ({model_count} model(s) in schema)."
            )
            Console.info("Next: pip install -r requirements.txt")
            Console.info("Then: tpy migrate && tpy seed && tpy serve")
            Console.info(
                "Default login: admin@example.com / admin123 "
                "(super-admin)"
            )
            Console.info(
                "Admin dashboard roles: super-admin, developer "
                "(run tpy admin to refresh UI)"
            )
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1)
