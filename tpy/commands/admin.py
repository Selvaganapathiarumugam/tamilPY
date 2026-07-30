from pathlib import Path

import typer

from tpy.generator.admin_generator import AdminGenerator
from tpy.runtime.builder import Builder
from tpy.utils.console import Console

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"


def prompt_api_base_url(
    api_base_url: str | None,
) -> str:
    """Ask for the backend base URL when one was not provided."""
    if api_base_url:
        return api_base_url.strip().rstrip("/")

    return typer.prompt(
        "FastAPI backend base URL",
        default=DEFAULT_API_BASE_URL,
    ).strip().rstrip("/")


def generate_admin(
    project_root: Path | str = ".",
    api_base_url: str | None = None,
    *,
    theme_name: str | None = None,
) -> int:
    """
    Parse schema.tpy once and generate the React admin dashboard.
    """
    root = Path(project_root)

    if not (root / "schema.tpy").exists():
        Console.error("schema.tpy not found. Run this inside a TPY project.")
        raise typer.Exit(1)

    base_url = prompt_api_base_url(api_base_url)
    admin_dir = root / "admin"

    if admin_dir.exists():
        Console.warning(
            "admin/ already exists; generated admin files will be overwritten."
        )

    builder = Builder(project_root=root)
    ast = builder.parse_schema()
    AdminGenerator(root).generate(
        ast,
        base_url,
        theme_name=theme_name,
    )
    return len(ast.models)


def register(app: typer.Typer) -> None:
    """Register the admin dashboard generation command."""

    @app.command("admin")
    def admin(
        api_base_url: str | None = typer.Option(
            None,
            "--api-base-url",
            help="FastAPI backend base URL for the generated admin app.",
        ),
        template: str | None = typer.Option(
            None,
            "--template",
            "-t",
            help="Apply starter template admin theme (or use admin-theme.json).",
        ),
    ) -> None:
        """
        Generate a Vite + React admin dashboard from ``schema.tpy``.
        """
        try:
            Console.info("Generating React admin dashboard...")
            model_count = generate_admin(
                project_root=Path("."),
                api_base_url=api_base_url,
                theme_name=template,
            )
            Console.success(
                f"Admin dashboard generated for {model_count} model(s)."
            )
            Console.info("Next: cd admin && npm install && npm run dev")
            Console.info("Keep the API running with: tpy serve")
        except typer.Exit:
            raise
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1) from error
