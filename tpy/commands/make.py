"""CLI commands: ``tpy make:model``, ``make:controller``, ``make:service``."""

from __future__ import annotations

from pathlib import Path

import typer

from tpy.exceptions import GeneratedFileConflict, TpyError
from tpy.generator.make_generator import MakeGenerator
from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register incremental make commands."""

    @app.command("make:model")
    def make_model(
        name: str = typer.Argument(..., help="Model class name (PascalCase)."),
        fields: str | None = typer.Option(
            None,
            "--fields",
            help=(
                'Comma-separated fields, e.g. '
                '"amount:float,status:enum(draft,paid)"'
            ),
        ),
        force: bool = typer.Option(
            False,
            "--force",
            help="Overwrite generated files that have manual edits.",
        ),
    ) -> None:
        """
        Append a model to ``schema.tpy`` and generate only that model's files.
        """
        try:
            model = MakeGenerator(Path("."), force=force).make_model(
                name,
                fields=fields,
            )
            Console.success(
                f"Model '{model.name}' added "
                f"({len(model.fields)} field(s))."
            )
            Console.info("Next: tpy migrate")
        except GeneratedFileConflict as error:
            Console.error(str(error))
            raise typer.Exit(1) from error
        except (TpyError, FileNotFoundError, ValueError) as error:
            Console.error(str(error))
            raise typer.Exit(1) from error

    @app.command("make:controller")
    def make_controller(
        name: str = typer.Argument(..., help="Existing model name."),
        force: bool = typer.Option(
            False,
            "--force",
            help="Overwrite generated files that have manual edits.",
        ),
    ) -> None:
        """Regenerate only the controller for an existing model."""
        try:
            model = MakeGenerator(Path("."), force=force).make_controller(name)
            Console.success(f"Controller regenerated for '{model.name}'.")
        except GeneratedFileConflict as error:
            Console.error(str(error))
            raise typer.Exit(1) from error
        except (TpyError, FileNotFoundError, ValueError) as error:
            Console.error(str(error))
            raise typer.Exit(1) from error

    @app.command("make:service")
    def make_service(
        name: str = typer.Argument(..., help="Existing model name."),
        force: bool = typer.Option(
            False,
            "--force",
            help="Overwrite generated files that have manual edits.",
        ),
    ) -> None:
        """Regenerate only the service for an existing model."""
        try:
            model = MakeGenerator(Path("."), force=force).make_service(name)
            Console.success(f"Service regenerated for '{model.name}'.")
        except GeneratedFileConflict as error:
            Console.error(str(error))
            raise typer.Exit(1) from error
        except (TpyError, FileNotFoundError, ValueError) as error:
            Console.error(str(error))
            raise typer.Exit(1) from error
