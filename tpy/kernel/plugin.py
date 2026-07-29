"""
Plugin contract and discovery.
"""

from __future__ import annotations

from abc import ABC
from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Iterable

from tpy.kernel.exceptions import PluginError
from tpy.kernel.provider import ServiceProvider

if TYPE_CHECKING:
    from tpy.kernel.application import Application

ENTRY_POINT_GROUP = "tamilpy.plugins"


class Plugin(ABC):
    """
    Distributable extension that contributes providers and hooks.

    Subclass and expose via package entry point::

        [project.entry-points."tamilpy.plugins"]
        billing = "billing_plugin:BillingPlugin"
    """

    name: str = "plugin"
    providers: list[type[ServiceProvider]] = []

    def register(self, app: Application) -> None:
        """Optional hook during application registration."""
        return None

    def boot(self, app: Application) -> None:
        """Optional hook during application boot."""
        return None


def discover_plugins(group: str = ENTRY_POINT_GROUP) -> list[Plugin]:
    """
    Load plugins from importlib entry points.

    Returns:
        Instantiated plugin objects.

    Raises:
        PluginError: When an entry point cannot be loaded.
    """
    plugins: list[Plugin] = []
    try:
        selected = entry_points(group=group)
    except TypeError:
        # Python < 3.10 style (not expected on 3.12, kept defensive)
        selected = entry_points().get(group, [])  # type: ignore[assignment]

    for ep in selected:
        try:
            loaded = ep.load()
        except Exception as error:  # noqa: BLE001 — surface as PluginError
            raise PluginError(
                f"Failed to load plugin entry point '{ep.name}': {error}"
            ) from error
        plugin = loaded() if isinstance(loaded, type) else loaded
        if not isinstance(plugin, Plugin):
            raise PluginError(
                f"Entry point '{ep.name}' did not produce a Plugin instance"
            )
        plugins.append(plugin)
    return plugins


def iter_plugin_providers(plugins: Iterable[Plugin]) -> list[ServiceProvider]:
    """Instantiate providers declared on plugins."""
    providers: list[ServiceProvider] = []
    for plugin in plugins:
        for provider_cls in plugin.providers:
            providers.append(provider_cls())
    return providers
