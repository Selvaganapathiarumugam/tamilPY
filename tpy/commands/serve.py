from pathlib import Path
import os
import sys

import typer

from tpy.config.loader import ConfigLoader
from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the serve command."""

    @app.command("serve")
    def serve(
        host: str | None = typer.Option(None, help="Bind host"),
        port: int | None = typer.Option(None, help="Bind port"),
        reload: bool = typer.Option(True, help="Enable auto-reload"),
    ) -> None:
        """
        Start the FastAPI development server.

        Expects ``app/main.py`` exposing ``app`` (uvicorn target: ``app.main:app``).
        """
        import uvicorn

        root = Path(".").resolve()
        main_file = root / "app" / "main.py"

        if not main_file.exists():
            Console.error(
                "app/main.py not found. Run this inside a TPY project "
                "(or run: tpy crud)."
            )
            raise typer.Exit(1)

        root_str = str(root)
        os.chdir(root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

        settings = ConfigLoader(root).load()
        bind_host = host or settings.host
        bind_port = port or settings.port

        try:
            from importlib.metadata import version as pkg_version

            Console.banner(pkg_version("tamilPY"))
        except Exception:
            from tpy import __version__

            Console.banner(__version__)
        Console.rule(settings.name)
        Console.info(f"Serving on http://{bind_host}:{bind_port}")
        if reload:
            Console.info("Auto-reload enabled")

        uvicorn.run(
            "app.main:app",
            host=bind_host,
            port=bind_port,
            reload=reload,
            app_dir=root_str,
            reload_dirs=[root_str],
        )
