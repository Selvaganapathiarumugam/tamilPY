"""
CLI commands for cache management.
"""

from __future__ import annotations

from pathlib import Path

import typer

from tpy.utils.console import Console

cache_app = typer.Typer(help="Manage application cache.")


def register(app: typer.Typer) -> None:
    """Register ``tpy cache`` subcommands."""
    app.add_typer(cache_app, name="cache")


@cache_app.command("clear")
def cache_clear(
    driver: str = typer.Option(
        "file",
        "--driver",
        "-d",
        help="Cache driver: file | memory | redis",
    ),
    redis_url: str = typer.Option(
        "redis://localhost:6379/0",
        "--redis-url",
        help="Redis URL when --driver=redis",
    ),
    path: str = typer.Option(
        "storage/framework/cache",
        "--path",
        help="Directory for file cache",
    ),
) -> None:
    """Flush the selected cache store."""
    from tpy.cache import Cache, FileStore, MemoryStore

    name = driver.lower()
    if name == "memory":
        Cache(MemoryStore()).flush()
        Console.success("Memory cache flushed (new empty store).")
        return
    if name == "file":
        store = FileStore(Path(path))
        Cache(store).flush()
        Console.success(f"File cache cleared: {path}")
        return
    if name == "redis":
        from tpy.cache.redis_store import RedisStore

        Cache(RedisStore(redis_url=redis_url)).flush()
        Console.success("Redis cache flushed.")
        return
    Console.error(f"Unknown cache driver: {driver}")
    raise typer.Exit(1)
