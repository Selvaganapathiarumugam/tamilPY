from pathlib import Path

import typer
import uvicorn

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
        """
        root = Path(".")
        main_file = root / "main.py"

        if not main_file.exists():
            Console.error("main.py not found. Run this inside a TPY project.")
            raise typer.Exit(1)

        settings = ConfigLoader(root).load()
        bind_host = host or settings.host
        bind_port = port or settings.port

        Console.info(
            f"Serving {settings.name} on http://{bind_host}:{bind_port}"
        )

        uvicorn.run(
            "main:app",
            host=bind_host,
            port=bind_port,
            reload=reload,
        )
