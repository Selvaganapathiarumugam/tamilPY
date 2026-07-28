"""
CLI entrypoint with lazy command registration.
"""

from __future__ import annotations

import importlib
import pkgutil

import typer

from tpy.exceptions import TpyError

app = typer.Typer(
    help="tamilPY — schema-driven Python web framework",
    no_args_is_help=True,
)


def _register_commands() -> None:
    import tpy.commands as commands_pkg

    for _, module_name, _ in pkgutil.iter_modules(commands_pkg.__path__):
        module = importlib.import_module(f"tpy.commands.{module_name}")
        if hasattr(module, "register"):
            module.register(app)


_register_commands()


@app.callback()
def _root() -> None:
    """tamilPY CLI."""


def main() -> None:
    """Console-script entry that maps framework errors to clean exits."""
    try:
        app()
    except TpyError as error:
        from tpy.utils.console import Console

        Console.error(str(error))
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
