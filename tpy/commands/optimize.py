"""
Optimize command — cache config and routes for production boots.
"""

from __future__ import annotations

from pathlib import Path

import typer

from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the optimize command."""

    @app.command("optimize")
    def optimize(
        app_path: str = typer.Option(
            "app.main:app",
            "--app",
            help="FastAPI import path for route cache",
        ),
        skip_routes: bool = typer.Option(
            False,
            "--skip-routes",
            help="Only cache configuration",
        ),
    ) -> None:
        """
        Cache configuration (and routes) for faster production startup.

        Sets you up for ``TPY_CONFIG_CACHE=1`` and ``tpy route list --cached``.
        """
        from tpy.config import Config
        from tpy.http.route_cache import RouteCache

        root = Path(".")
        Console.rule("tamilPY optimize")
        cfg = Config.load(root)
        config_path = cfg.cache()
        Console.success(f"Config cache → {config_path}")

        if skip_routes:
            Console.info("Skipped route cache (--skip-routes).")
            return

        try:
            from tpy.commands.route import _load_app

            fastapi_app = _load_app(app_path)
            route_path = RouteCache(root).dump(fastapi_app)
            count = len(RouteCache(root).load())
            Console.success(f"Route cache ({count}) → {route_path}")
        except typer.Exit:
            Console.warning(
                "Route cache skipped (app import failed). "
                "Run inside a project after tpy build."
            )
        Console.info("Tip: export TPY_CONFIG_CACHE=1 to prefer config cache at boot.")
