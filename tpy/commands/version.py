from importlib.metadata import PackageNotFoundError, version as pkg_version

import typer

from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the version command."""

    @app.command("version")
    def version() -> None:
        """Show the TPY framework version."""
        try:
            current = pkg_version("tamilPY")
        except PackageNotFoundError:
            current = "0.0.0 (not installed)"
        Console.info(f"tamilPY {current}")
