"""CLI: ``tpy studio`` — local visual schema builder."""

from __future__ import annotations

import webbrowser
from pathlib import Path

import typer
import uvicorn

from tpy.studio import studio_version
from tpy.studio.server import create_app, ui_dist_dir
from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the studio command."""

    @app.command("studio")
    def studio(
        port: int = typer.Option(4200, "--port", "-p", help="Listen port."),
        host: str = typer.Option(
            "127.0.0.1",
            "--host",
            help="Bind address (default localhost-only).",
        ),
        no_open: bool = typer.Option(
            False,
            "--no-open",
            help="Do not open a browser tab.",
        ),
        version: bool = typer.Option(
            False,
            "--version",
            help="Print Studio / tamilPY version and exit.",
        ),
        template: str | None = typer.Option(
            None,
            "--template",
            "-t",
            help="Pre-load a starter template schema in-memory until saved "
            "(writes schema.tpy only after Studio save).",
        ),
    ) -> None:
        """
        Start the local tamilPY Studio UI (schema designer + build console).
        """
        if version:
            Console.info(f"tamilPY Studio {studio_version()}")
            raise typer.Exit()

        root = Path(".").resolve()
        if not (root / "schema.tpy").exists() and template is None:
            Console.error(
                "schema.tpy not found. Run inside a TPY project "
                "or pass --template <name>."
            )
            raise typer.Exit(1)

        if template is not None and not (root / "schema.tpy").exists():
            from tpy.starter_templates import apply_template_files, get_template

            try:
                get_template(template)
            except KeyError as error:
                Console.error(str(error))
                raise typer.Exit(1) from error
            # Scaffold minimal project files if missing, then apply template.
            Console.info(f"Seeding project from template '{template}'...")
            apply_template_files(root, template)

        if host not in {"127.0.0.1", "localhost", "::1"}:
            Console.warning(
                f"Binding to {host} exposes Studio without auth on your "
                f"network. Prefer 127.0.0.1 unless you trust this network."
            )

        if not ui_dist_dir().exists():
            Console.warning(
                "Studio UI dist/ missing. API will run; build UI with: "
                "cd tpy/studio/ui && npm install && npm run build"
            )

        url = f"http://{host}:{port}"
        Console.info(f"Starting tamilPY Studio on {url}")
        Console.info(f"Project: {root}")

        if not no_open:
            webbrowser.open(url)

        uvicorn.run(
            create_app(root),
            host=host,
            port=port,
            log_level="info",
        )
