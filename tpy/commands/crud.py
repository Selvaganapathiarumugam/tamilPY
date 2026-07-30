from pathlib import Path

import typer

from tpy.runtime.builder import Builder
from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the CRUD generation command."""

    @app.command("crud")
    def crud() -> None:
        """
        Generate full CRUD layers from ``schema.tpy``.
        """
        try:
            Console.info("Generating CRUD from schema.tpy...")
            builder = Builder(project_root=Path("."))
            ast = builder.build()
            Console.success(
                f"CRUD generated for {len(ast.models)} model(s)."
            )
        except Exception as error:
            Console.error(str(error))
            raise typer.Exit(1) from error
