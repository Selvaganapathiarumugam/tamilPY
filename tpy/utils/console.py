"""
Enhanced console helpers (Rich-backed).
"""

from __future__ import annotations

import typer


class Console:
    """Framework CLI console output."""

    @staticmethod
    def info(message: str) -> None:
        typer.secho(message, fg=typer.colors.CYAN)

    @staticmethod
    def success(message: str) -> None:
        typer.secho(message, fg=typer.colors.GREEN)

    @staticmethod
    def warning(message: str) -> None:
        typer.secho(message, fg=typer.colors.YELLOW)

    @staticmethod
    def error(message: str) -> None:
        typer.secho(message, fg=typer.colors.RED)

    @staticmethod
    def rule(title: str = "") -> None:
        """Print a horizontal rule with optional title."""
        try:
            from rich.console import Console as RichConsole

            RichConsole().rule(title)
        except Exception:
            line = f"—— {title} ——" if title else "————————"
            typer.echo(line)

    @staticmethod
    def banner(version: str) -> None:
        """Print the tamilPY startup banner."""
        try:
            from rich.panel import Panel
            from rich.console import Console as RichConsole

            RichConsole().print(
                Panel.fit(
                    f"[bold cyan]tamilPY[/] [dim]v{version}[/]\n"
                    "[dim]Schema-driven Python framework[/]",
                    border_style="cyan",
                )
            )
        except Exception:
            typer.secho(f"tamilPY v{version}", fg=typer.colors.CYAN, bold=True)

    @staticmethod
    def table(headers: list[str], rows: list[list[str]], title: str = "") -> None:
        """Print a simple table."""
        try:
            from rich.console import Console as RichConsole
            from rich.table import Table

            table = Table(title=title or None, show_header=True)
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*[str(cell) for cell in row])
            RichConsole().print(table)
        except Exception:
            if title:
                typer.echo(title)
            typer.echo(" | ".join(headers))
            for row in rows:
                typer.echo(" | ".join(str(cell) for cell in row))
