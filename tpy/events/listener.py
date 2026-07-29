"""
Listener contract for the event bus.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from tpy.events.event import Event


class Listener(ABC):
    """
    Synchronous event listener.

    Prefer subclassing for reusable listeners; callables are also accepted by
    ``EventDispatcher.listen``.
    """

    @abstractmethod
    def handle(self, event: Event) -> Any:
        """Handle ``event``. Return a value to support ``dispatch_until``."""
