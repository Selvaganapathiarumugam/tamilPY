"""
Base event type for the tamilPY event bus.
"""

from __future__ import annotations


class Event:
    """
    Base class for domain / application events.

    Call ``stop()`` inside a listener to halt further propagation for the
    current ``dispatch`` call.
    """

    def __init__(self) -> None:
        self._stopped = False

    @property
    def stopped(self) -> bool:
        """Return whether propagation was stopped."""
        return self._stopped

    def stop(self) -> None:
        """Stop remaining listeners for this dispatch."""
        self._stopped = True
