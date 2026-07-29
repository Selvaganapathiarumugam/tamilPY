"""
CLI commands for route cache.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import typer

from tpy.utils.console import Console

route_app = typer.Typer(help="Cache and inspect HTTP routes.")


def register(app: typer.Typer) -> None:
    """Register ``tpy route`` subcommands."""
    app.add_typer(route_app, name="route")


@route_app.command("cache")
def route_cache(
    app_path: str = typer.Option(
        "app.main:app",
        "--app",
        help="Import path to FastAPI app (module:attr)",
    ),
) -> None:
    """Write ``storage/framework/routes.cache.json`` from the live app."""
    from tpy.http.route_cache import RouteCache

    fastapi_app = _load_app(app_path)
    path = RouteCache(Path(".")).dump(fastapi_app)
    count = len(RouteCache(Path(".")).load())
    Console.success(f"Cached {count} route(s) → {path}")


@route_app.command("clear")
def route_clear() -> None:
    """Delete the route cache file."""
    from tpy.http.route_cache import RouteCache

    if RouteCache(Path(".")).clear():
        Console.success("Route cache cleared.")
    else:
        Console.warning("No route cache file found.")


@route_app.command("list")
def route_list(
    cached: bool = typer.Option(
        False,
        "--cached",
        help="List from cache file instead of importing the app",
    ),
    app_path: str = typer.Option(
        "app.main:app",
        "--app",
        help="Import path when not using --cached",
    ),
) -> None:
    """List application routes."""
    from tpy.http.route_cache import RouteCache

    cache = RouteCache(Path("."))
    if cached:
        routes = cache.load()
        if not routes:
            Console.warning("Route cache empty. Run: tpy route cache")
            return
    else:
        fastapi_app = _load_app(app_path)
        routes = RouteCache.collect(fastapi_app)

    for route in routes:
        methods = ",".join(route.get("methods") or ["*"])
        Console.info(f"{methods:15} {route.get('path')}  ({route.get('name')})")


def _load_app(app_path: str):
    if ":" not in app_path:
        Console.error("App path must look like module:attr (e.g. app.main:app)")
        raise typer.Exit(1)
    module_name, _, attr = app_path.partition(":")
    try:
        module = importlib.import_module(module_name)
        return getattr(module, attr)
    except Exception as error:  # noqa: BLE001
        Console.error(f"Unable to import '{app_path}': {error}")
        raise typer.Exit(1) from error
