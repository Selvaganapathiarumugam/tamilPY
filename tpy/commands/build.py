from pathlib import Path

import typer

from tpy.runtime.builder import Builder
from tpy.generator.admin_generator import AdminGenerator
from tpy.utils.console import Console
from tpy.utils.db_wizard import DatabaseWizard
from tpy.commands.admin import prompt_api_base_url


def register(app: typer.Typer) -> None:
    """Register the build command."""

    @app.command("build")
    def build(
        skip_db: bool = typer.Option(
            False,
            "--skip-db",
            help="Skip interactive database setup and use existing .env",
        ),
        with_ui: bool = typer.Option(
            False,
            "--with-ui",
            help="Also generate the React admin dashboard under admin/",
        ),
        api_base_url: str | None = typer.Option(
            None,
            "--api-base-url",
            help="FastAPI backend base URL for --with-ui.",
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
            if with_ui:
                base_url = prompt_api_base_url(api_base_url)
                if (root / "admin").exists():
                    Console.warning(
                        "admin/ already exists; generated admin files will be overwritten."
                    )
                AdminGenerator(root).generate(ast, base_url)

            model_count = len(ast.models)
            Console.success(
                f"Build completed successfully ({model_count} model(s))."
            )
            if with_ui:
                Console.info(
                    "Next: tpy migrate && tpy seed && tpy serve, then cd admin && npm install && npm run dev"
                )
            else:
                Console.info("Next: tpy migrate && tpy seed && tpy serve")
        except FileNotFoundError as error:
            Console.error(str(error))
            raise typer.Exit(1)
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1)
