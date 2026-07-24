from pathlib import Path

import typer

from tpy.runtime.builder import Builder
from tpy.utils.console import Console
from tpy.utils.db_wizard import DatabaseWizard


def register(app: typer.Typer) -> None:
    """Register the build command."""

    @app.command("build")
    def build(
        skip_db: bool = typer.Option(
            False,
            "--skip-db",
            help="Skip interactive database setup and use existing .env",
        ),
    ) -> None:
        """
        Configure database, parse schema.tpy, and generate the application.
        """
        root = Path(".")

        if not (root / "schema.tpy").exists():
            Console.error("schema.tpy not found. Run this inside a TPY project.")
            raise typer.Exit(1)

        try:
            Console.info("Starting TPY build...")

            if not skip_db:
                Console.info("Step 1/2 — Database configuration")
                DatabaseWizard(root).run()
                Console.info("")
                Console.info("Step 2/2 — Generating application code")
            else:
                Console.info("Using existing database configuration (--skip-db)")

            builder = Builder(project_root=root)
            ast = builder.build()
            model_count = len(ast.models)
            Console.success(
                f"Build completed successfully ({model_count} model(s))."
            )
            Console.info("Next: tpy migrate && tpy seed && tpy serve")
        except FileNotFoundError as error:
            Console.error(str(error))
            raise typer.Exit(1)
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1)
