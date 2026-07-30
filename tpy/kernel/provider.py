"""
Service provider contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tpy.kernel.application import Application


class ServiceProvider:
    """
    Register and boot services into the application container.

    Lifecycle:
    1. ``register`` — bind services (no resolving of other deferred providers)
    2. ``boot`` — after all providers registered
    """

    def register(self, app: Application) -> None:
        """Bind services into ``app.container``."""
        return None

    def boot(self, app: Application) -> None:
        """Run after the container is fully registered."""
        return None
