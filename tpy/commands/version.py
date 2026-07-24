import typer

from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the version command."""

    @app.command("version")
    def version() -> None:
        """Show the TPY framework version."""
        Console.info("tamilPY 0.1.0")
