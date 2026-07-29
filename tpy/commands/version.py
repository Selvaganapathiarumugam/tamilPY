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
            from tpy import __version__

            current = f"{__version__} (editable / not installed)"
        Console.banner(current)
        Console.info(f"tamilPY {current}")
