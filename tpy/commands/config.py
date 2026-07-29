"""
CLI commands for configuration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer

from tpy.utils.console import Console

config_app = typer.Typer(help="Inspect and cache application configuration.")


def register(app: typer.Typer) -> None:
    """Register ``tpy config`` subcommands."""
    app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show(
    key: str | None = typer.Argument(None, help="Optional dotted key"),
    cached: bool = typer.Option(
        False,
        "--cached",
        help="Prefer config cache when fresh (or set TPY_CONFIG_CACHE=1)",
    ),
) -> None:
    """Show config (all or one key)."""
    from tpy.config import Config

    cfg = Config.load_auto(Path("."), prefer_cache=True if cached else None)
    if key:
        value = cfg.get(key)
        if value is None and not cfg.has(key):
            Console.error(f"Missing config key: {key}")
            raise typer.Exit(1)
        Console.info(json.dumps(value, indent=2, default=str))
        return
    Console.info(json.dumps(cfg.all(), indent=2, default=str))


@config_app.command("cache")
def config_cache() -> None:
    """Write ``storage/framework/config.cache.json`` for faster boots."""
    from tpy.config import Config

    path = Config.load(Path(".")).cache()
    Console.success(f"Config cached at {path}")
    Console.info("Tip: export TPY_CONFIG_CACHE=1 to load from cache at boot.")


@config_app.command("clear")
def config_clear() -> None:
    """Remove the config cache file."""
    from tpy.config import Config

    removed = Config.load(Path(".")).clear_cache()
    if removed:
        Console.success("Config cache cleared.")
    else:
        Console.warning("No config cache file found.")


@config_app.command("status")
def config_status() -> None:
    """Show whether the config cache exists and is fresh."""
    from tpy.config import Config

    cfg = Config(base_path=Path("."))
    prefer = Config.prefer_cache_enabled()
    rows = [
        ["Cache file", str(cfg.cache_path())],
        ["Exists", "yes" if cfg.is_cached() else "no"],
        ["Fresh", "yes" if cfg.cache_is_fresh() else "no"],
        ["TPY_CONFIG_CACHE", os.getenv("TPY_CONFIG_CACHE") or "(unset)"],
        ["Prefer cache", "yes" if prefer else "no"],
    ]
    Console.table(["Key", "Value"], rows, title="Config cache")
