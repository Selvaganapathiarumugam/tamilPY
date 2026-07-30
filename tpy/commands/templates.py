"""CLI: ``tpy templates list`` / ``tpy templates show``."""

from __future__ import annotations

import typer

from tpy.starter_templates import get_template, list_templates, read_schema
from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the templates subcommand group."""
    templates_app = typer.Typer(
        help="List and inspect starter templates.",
        no_args_is_help=True,
    )
    app.add_typer(templates_app, name="templates")

    @templates_app.command("list")
    def templates_list() -> None:
        """List available starter templates."""
        items = list_templates()
        if not items:
            Console.warning("No starter templates found.")
            return
        for info in items:
            models = ", ".join(info.models)
            Console.info(f"{info.name:18} {info.description}")
            Console.info(f"{'':18} models: {models}")

    @templates_app.command("show")
    def templates_show(
        name: str = typer.Argument(..., help="Template name."),
    ) -> None:
        """Print the ``schema.tpy`` that a template would install."""
        try:
            get_template(name)
        except KeyError as error:
            Console.error(str(error))
            raise typer.Exit(1) from error
        typer.echo(read_schema(name), nl=False)
