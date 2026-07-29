"""
Built-in framework service providers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tpy.events import EventDispatcher, event_dispatcher
from tpy.http.builtin_middleware import RequestIdMiddleware
from tpy.http.health import HealthChecker
from tpy.http.lifecycle import Lifecycle
from tpy.http.middleware import MiddlewareManager
from tpy.kernel.provider import ServiceProvider

if TYPE_CHECKING:
    from tpy.kernel.application import Application


class FrameworkServiceProvider(ServiceProvider):
    """Bind core framework services."""

    def register(self, app: Application) -> None:
        app.instance("app", app)
        app.instance("path", app.base_path)
        app.singleton(
            "events",
            lambda c: event_dispatcher(),
        )
        app.alias("events", EventDispatcher)
        if not app.has("middleware"):
            manager = MiddlewareManager()
            manager.register("request_id", RequestIdMiddleware)
            manager.append("api", "request_id")
            app.instance("middleware", manager)
        if not app.has("lifecycle"):
            app.instance("lifecycle", Lifecycle())
        if not app.has("health"):
            health = HealthChecker()
            health.add("app", lambda: True)
            app.instance("health", health)
        if not app.has("config"):
            from tpy.config import Config

            app.instance("config", Config.load_auto(app.base_path))
        if not app.has("log"):
            from tpy.logging import LogManager

            logs = LogManager()
            cfg = app.make("config") if app.has("config") else None
            level = "INFO"
            if cfg is not None:
                level = str(cfg.get("logging.level", "INFO"))
            logs.configure(
                level=level,
                log_dir=app.base_path / "storage" / "logs",
                app_name=str(
                    cfg.get("app.name", "app") if cfg is not None else "app"
                ),
            )
            app.instance("log", logs)
        if not app.has("storage"):
            from tpy.storage import Storage

            app.instance("storage", Storage.default(app.base_path))


class HttpServiceProvider(ServiceProvider):
    """
    HTTP middleware, lifecycle, and health check services.
    """

    def register(self, app: Application) -> None:
        manager = MiddlewareManager()
        manager.register("request_id", RequestIdMiddleware)
        manager.append("api", "request_id")
        app.instance("middleware", manager)
        app.instance("lifecycle", Lifecycle())
        health = HealthChecker()
        health.add("app", lambda: True)
        app.instance("health", health)


class EventsServiceProvider(ServiceProvider):
    """
    Ensure a dedicated ``EventDispatcher`` is available.

    Prefer this when you want an app-scoped dispatcher instead of the
    process singleton.
    """

    def register(self, app: Application) -> None:
        app.singleton("events", lambda c: EventDispatcher())
        app.alias("events", EventDispatcher)
