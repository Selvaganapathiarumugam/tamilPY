"""
About / environment diagnostics for the CLI.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

import typer

from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register about and commands listing."""

    @app.command("about")
    def about() -> None:
        """Show framework version and local environment."""
        from tpy import __version__

        try:
            from importlib.metadata import version as pkg_version

            installed = pkg_version("tamilPY")
        except Exception:
            installed = __version__

        root = Path(".").resolve()
        is_project = (root / "schema.tpy").exists() and (root / "tpy.toml").exists()
        rows = [
            ["Package", installed],
            ["Python", sys.version.split()[0]],
            ["Platform", platform.platform()],
            ["CWD", str(root)],
            ["TPY project", "yes" if is_project else "no"],
        ]
        if is_project:
            from tpy.config import Config

            cfg = Config.load_auto(root)
            rows.append(["App name", str(cfg.get("app.name", "-"))])
            rows.append(
                ["Config cache", "fresh" if cfg.cache_is_fresh() else "no/stale"]
            )
            rows.append(
                [
                    "Route cache",
                    "yes"
                    if (root / "storage" / "framework" / "routes.cache.json").exists()
                    else "no",
                ]
            )

        Console.banner(installed)
        Console.table(["Key", "Value"], rows, title="Environment")

    @app.command("commands")
    def list_commands() -> None:
        """List registered CLI commands."""
        click_app = typer.main.get_command(app)
        names = sorted(click_app.list_commands(None))  # type: ignore[arg-type]
        rows: list[list[str]] = []
        for name in names:
            cmd = click_app.get_command(None, name)  # type: ignore[arg-type]
            help_text = ((cmd.help if cmd else None) or "").split("\n")[0]
            rows.append([name, help_text])
        Console.table(["Command", "Description"], rows, title="tamilPY CLI")
