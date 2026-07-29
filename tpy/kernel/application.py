"""
Application kernel — dual-mode FastAPI bootstrap.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Self

from tpy.kernel.container import Container
from tpy.kernel.exceptions import ProviderError
from tpy.kernel.plugin import (
    Plugin,
    discover_plugins,
)
from tpy.kernel.provider import ServiceProvider
from tpy.kernel.providers import FrameworkServiceProvider


class Application:
    """
    tamilPY application kernel.

    Dual-mode:
    - ``create()`` builds and returns a new FastAPI app (recommended)
    - ``mount(fastapi_app)`` registers services onto an existing FastAPI app
    """

    def __init__(self, base_path: Path | str = ".") -> None:
        self.base_path = Path(base_path).resolve()
        self.container = Container()
        self._providers: list[ServiceProvider] = []
        self._plugins: list[Plugin] = []
        self._booted = False
        self._fastapi: Any | None = None
        self.options: dict[str, Any] = {}
        self._middleware_groups_to_apply: list[str] = []
        self._enable_health_routes = True
        self._enable_lifecycle = True

        # Core bindings available immediately
        self.instance("app", self)
        self.instance("path", self.base_path)

    # ----- container sugar -----

    def bind(self, abstract: str | type, concrete, *, shared: bool = False) -> Self:
        self.container.bind(abstract, concrete, shared=shared)
        return self

    def singleton(self, abstract: str | type, concrete) -> Self:
        self.container.singleton(abstract, concrete)
        return self

    def instance(self, abstract: str | type, obj: Any) -> Self:
        self.container.instance(abstract, obj)
        return self

    def alias(self, abstract: str | type, alias: str | type) -> Self:
        self.container.alias(abstract, alias)
        return self

    def make(self, abstract: str | type) -> Any:
        """Resolve a service from the container."""
        return self.container.make(abstract)

    def has(self, abstract: str | type) -> bool:
        return self.container.has(abstract)

    # ----- providers & plugins -----

    def register(
        self,
        provider: ServiceProvider | type[ServiceProvider],
    ) -> Self:
        """Register a service provider (instantiates classes)."""
        instance = provider() if isinstance(provider, type) else provider
        if not isinstance(instance, ServiceProvider):
            raise ProviderError(
                f"{type(instance).__name__} is not a ServiceProvider"
            )
        self._providers.append(instance)
        return self

    def register_plugin(self, plugin: Plugin | type[Plugin]) -> Self:
        """Register a plugin and its declared providers."""
        instance = plugin() if isinstance(plugin, type) else plugin
        if not isinstance(instance, Plugin):
            raise ProviderError(f"{type(instance).__name__} is not a Plugin")
        self._plugins.append(instance)
        for provider_cls in instance.providers:
            self.register(provider_cls)
        return self

    def load_plugins(self, group: str = "tamilpy.plugins") -> Self:
        """Discover and register plugins from entry points."""
        for plugin in discover_plugins(group=group):
            self.register_plugin(plugin)
        return self

    def with_framework_providers(self) -> Self:
        """Register default framework providers (events, app bindings)."""
        return self.register(FrameworkServiceProvider)

    def middleware_groups(self, *groups: str) -> Self:
        """
        Queue middleware groups to apply when ``create`` / ``mount`` runs.

        Example::

            Application(".").middleware_groups("api").create()
        """
        self._middleware_groups_to_apply.extend(groups)
        return self

    @property
    def middleware(self):
        """
        Resolve the ``MiddlewareManager`` (registers defaults if needed).
        """
        if not self.has("middleware"):
            from tpy.http.builtin_middleware import RequestIdMiddleware
            from tpy.http.middleware import MiddlewareManager

            manager = MiddlewareManager()
            manager.register("request_id", RequestIdMiddleware)
            manager.append("api", "request_id")
            self.instance("middleware", manager)
        return self.make("middleware")

    @property
    def lifecycle(self):
        """Resolve the ``Lifecycle`` hook registry."""
        if not self.has("lifecycle"):
            from tpy.http.lifecycle import Lifecycle

            self.instance("lifecycle", Lifecycle())
        return self.make("lifecycle")

    @property
    def health(self):
        """Resolve the ``HealthChecker``."""
        if not self.has("health"):
            from tpy.http.health import HealthChecker

            checker = HealthChecker()
            checker.add("app", lambda: True)
            self.instance("health", checker)
        return self.make("health")

    @property
    def config(self):
        """Resolve the ``Config`` manager."""
        if not self.has("config"):
            from tpy.config import Config

            self.instance("config", Config.load_auto(self.base_path))
        return self.make("config")

    @property
    def log(self):
        """Resolve the ``LogManager``."""
        if not self.has("log"):
            from tpy.logging import LogManager

            manager = LogManager()
            manager.configure(log_dir=self.base_path / "storage" / "logs")
            self.instance("log", manager)
        return self.make("log")

    @property
    def storage(self):
        """Resolve the ``Storage`` manager."""
        if not self.has("storage"):
            from tpy.storage import Storage

            self.instance("storage", Storage.default(self.base_path))
        return self.make("storage")

    def without_health_routes(self) -> Self:
        """Disable automatic ``/health`` route registration on mount."""
        self._enable_health_routes = False
        return self

    def without_lifecycle(self) -> Self:
        """Disable automatic lifecycle wiring on mount."""
        self._enable_lifecycle = False
        return self

    # ----- boot / FastAPI -----

    def boot(self) -> Self:
        """
        Run provider/plugin ``register`` then ``boot`` hooks.

        Idempotent: subsequent calls are no-ops.
        """
        if self._booted:
            return self

        for provider in self._providers:
            provider.register(self)
        for plugin in self._plugins:
            plugin.register(self)

        for provider in self._providers:
            provider.boot(self)
        for plugin in self._plugins:
            plugin.boot(self)

        self._booted = True
        return self

    def create(
        self,
        *,
        title: str | None = None,
        load_entry_plugins: bool = False,
        use_framework_providers: bool = True,
        **fastapi_kwargs: Any,
    ) -> Any:
        """
        Boot the kernel and return a new ``FastAPI`` instance.

        The FastAPI app is also stored on ``app.state.tpy`` and bound as
        ``fastapi`` in the container.
        """
        from fastapi import FastAPI

        if use_framework_providers and not any(
            isinstance(p, FrameworkServiceProvider) for p in self._providers
        ):
            self.with_framework_providers()
        if load_entry_plugins:
            self.load_plugins()

        self.boot()
        kwargs = dict(fastapi_kwargs)
        if title is not None:
            kwargs.setdefault("title", title)
        fastapi_app = FastAPI(**kwargs)
        return self.mount(fastapi_app)

    def mount(self, fastapi_app: Any) -> Any:
        """
        Attach this kernel to an existing FastAPI app (dual-mode).

        Sets ``fastapi_app.state.tpy = self`` and binds ``fastapi`` in the
        container. Boots the kernel if not already booted.
        """
        if not self._booted:
            if not any(
                isinstance(p, FrameworkServiceProvider) for p in self._providers
            ):
                self.with_framework_providers()
            self.boot()

        self._fastapi = fastapi_app
        self.instance("fastapi", fastapi_app)
        state = getattr(fastapi_app, "state", None)
        if state is not None:
            state.tpy = self

        if self._middleware_groups_to_apply and self.has("middleware"):
            self.make("middleware").apply(
                fastapi_app, *self._middleware_groups_to_apply
            )

        if self._enable_lifecycle:
            from tpy.http.lifecycle import attach_lifecycle

            attach_lifecycle(fastapi_app, self.lifecycle)

        if self._enable_health_routes:
            from tpy.http.health import register_health_routes

            register_health_routes(fastapi_app, self.health)

        return fastapi_app

    @property
    def plugins(self) -> list[Plugin]:
        """Registered plugins."""
        return list(self._plugins)

    @property
    def providers(self) -> list[ServiceProvider]:
        """Registered service providers."""
        return list(self._providers)

    @property
    def booted(self) -> bool:
        """Whether ``boot()`` has completed."""
        return self._booted


def create_app(
    base_path: Path | str = ".",
    **kwargs: Any,
) -> Any:
    """Shortcut: ``Application(base_path).create(**kwargs)``."""
    return Application(base_path).create(**kwargs)
