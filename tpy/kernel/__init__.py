"""
tamilPY application kernel (DI, providers, plugins).
"""

from tpy.kernel.application import Application, create_app
from tpy.kernel.container import Container
from tpy.kernel.exceptions import (
    BindingError,
    KernelError,
    PluginError,
    ProviderError,
)
from tpy.kernel.plugin import Plugin, discover_plugins
from tpy.kernel.provider import ServiceProvider
from tpy.kernel.providers import EventsServiceProvider, FrameworkServiceProvider, HttpServiceProvider

__all__ = [
    "Application",
    "BindingError",
    "Container",
    "EventsServiceProvider",
    "FrameworkServiceProvider",
    "HttpServiceProvider",
    "KernelError",
    "Plugin",
    "PluginError",
    "ProviderError",
    "ServiceProvider",
    "create_app",
    "discover_plugins",
]
