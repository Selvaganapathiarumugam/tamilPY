"""Tests for Application kernel, providers, and plugins."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI

from tpy.events import EventDispatcher
from tpy.kernel import (
    Application,
    BindingError,
    Container,
    Plugin,
    ServiceProvider,
    create_app,
)


class CounterService:
    def __init__(self) -> None:
        self.value = 0

    def inc(self) -> int:
        self.value += 1
        return self.value


class CounterProvider(ServiceProvider):
    def register(self, app: Application) -> None:
        app.singleton("counter", lambda c: CounterService())

    def boot(self, app: Application) -> None:
        app.make("counter").inc()


class DemoPlugin(Plugin):
    name = "demo"
    providers = [CounterProvider]

    def __init__(self) -> None:
        self.registered = False
        self.booted = False

    def register(self, app: Application) -> None:
        self.registered = True

    def boot(self, app: Application) -> None:
        self.booted = True


def test_container_singleton_and_alias():
    c = Container()
    c.singleton("counter", lambda container: CounterService())
    c.alias("counter", "c")
    a = c.make("counter")
    b = c.make("c")
    assert a is b
    assert c.has("counter")
    with pytest.raises(BindingError):
        c.make("missing")


def test_provider_register_and_boot(tmp_path: Path):
    app = Application(tmp_path)
    app.register(CounterProvider).boot()
    assert app.make("counter").value == 1
    app.boot()  # idempotent
    assert app.make("counter").value == 1


def test_plugin_registers_providers(tmp_path: Path):
    plugin = DemoPlugin()
    app = Application(tmp_path)
    app.register_plugin(plugin).boot()
    assert plugin.registered and plugin.booted
    assert app.make("counter").value == 1


def test_create_returns_fastapi(tmp_path: Path):
    fastapi_app = Application(tmp_path).create(title="Demo")
    assert isinstance(fastapi_app, FastAPI)
    assert fastapi_app.title == "Demo"
    assert fastapi_app.state.tpy.booted
    assert isinstance(fastapi_app.state.tpy.make("events"), EventDispatcher)


def test_mount_dual_mode(tmp_path: Path):
    existing = FastAPI(title="Raw")
    kernel = Application(tmp_path)
    kernel.register(CounterProvider)
    mounted = kernel.mount(existing)
    assert mounted is existing
    assert existing.state.tpy is kernel
    assert kernel.make("counter").value == 1


def test_create_app_shortcut(tmp_path: Path):
    app = create_app(tmp_path, title="X")
    assert isinstance(app, FastAPI)
    assert app.title == "X"
