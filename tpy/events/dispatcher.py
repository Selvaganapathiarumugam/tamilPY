"""
Synchronous event dispatcher.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from tpy.events.event import Event
from tpy.events.listener import Listener

ListenerCallable = Callable[[Event], Any]
ListenerLike = Listener | ListenerCallable

_WILDCARD = "*"


class EventDispatcher:
    """
    Sync pub/sub dispatcher.

    Listeners run in registration order. Exceptions propagate immediately
    (fail-fast). Use ``event.stop()`` or ``dispatch_until`` for short-circuit.
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[ListenerLike]] = defaultdict(list)

    def listen(
        self,
        event_type: type[Event] | str,
        listener: ListenerLike,
    ) -> EventDispatcher:
        """
        Register ``listener`` for ``event_type``.

        Pass ``\"*\"`` to receive every event after typed listeners.
        """
        key = self._key(event_type)
        self._listeners[key].append(listener)
        return self

    def forget(self, event_type: type[Event] | str) -> None:
        """Remove all listeners for ``event_type``."""
        key = self._key(event_type)
        self._listeners.pop(key, None)

    def has_listeners(self, event_type: type[Event] | str) -> bool:
        """Return whether any listeners are registered for ``event_type``."""
        key = self._key(event_type)
        return bool(self._listeners.get(key)) or bool(
            self._listeners.get(_WILDCARD)
        )

    def dispatch(self, event: Event) -> Event:
        """
        Dispatch ``event`` to all matching listeners.

        Returns:
            The same event instance (may have ``stopped`` set).
        """
        for listener in self._resolve(event):
            if event.stopped:
                break
            self._invoke(listener, event)
        return event

    def dispatch_until(self, event: Event) -> Any:
        """
        Dispatch until a listener returns a non-``None`` value.

        Returns:
            First non-``None`` listener result, or ``None``.
        """
        for listener in self._resolve(event):
            if event.stopped:
                break
            result = self._invoke(listener, event)
            if result is not None:
                return result
        return None

    def _resolve(self, event: Event) -> list[ListenerLike]:
        typed = list(self._listeners.get(self._key(type(event)), []))
        wild = list(self._listeners.get(_WILDCARD, []))
        return typed + wild

    def _invoke(self, listener: ListenerLike, event: Event) -> Any:
        if isinstance(listener, Listener):
            return listener.handle(event)
        return listener(event)

    def _key(self, event_type: type[Event] | str) -> str:
        if isinstance(event_type, str):
            return event_type
        return f"{event_type.__module__}.{event_type.__qualname__}"


_default_dispatcher: EventDispatcher | None = None


def event_dispatcher() -> EventDispatcher:
    """Return the process-wide default ``EventDispatcher`` singleton."""
    global _default_dispatcher
    if _default_dispatcher is None:
        _default_dispatcher = EventDispatcher()
    return _default_dispatcher


def reset_event_dispatcher() -> None:
    """Reset the default singleton (intended for tests)."""
    global _default_dispatcher
    _default_dispatcher = None
