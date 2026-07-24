from pathlib import Path

import typer

from tpy.config.loader import ConfigLoader
from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the doctor command."""

    @app.command("doctor")
    def doctor() -> None:
        """
        Check that the current directory looks like a valid TPY project.
        """
        root = Path(".")
        required = [
            "schema.tpy",
            "tpy.toml",
            "main.py",
            "app/main.py",
            "app",
            "app/logger.py",
            "database",
            "database/seeds",
        ]

        ok = True
        for item in required:
            path = root / item
            if path.exists():
                Console.success(f"OK  {item}")
            else:
                Console.error(f"MISS {item}")
                ok = False

        settings = ConfigLoader(root).load()
        Console.info(
            f"Project={settings.name} database={settings.database}"
        )

        if not ok:
            raise typer.Exit(1)

        Console.success("TPY project looks healthy.")
