"""Tests for EventDispatcher."""

from __future__ import annotations

import pytest

from tpy.events import (
    Event,
    EventDispatcher,
    Listener,
    event_dispatcher,
)


class UserRegistered(Event):
    def __init__(self, user_id: str) -> None:
        super().__init__()
        self.user_id = user_id


class Recorder(Listener):
    def __init__(self, sink: list) -> None:
        self.sink = sink

    def handle(self, event: Event) -> None:
        assert isinstance(event, UserRegistered)
        self.sink.append(event.user_id)


def test_dispatch_calls_listeners_in_order() -> None:
    sink: list[str] = []
    dispatcher = EventDispatcher()
    dispatcher.listen(UserRegistered, Recorder(sink))
    dispatcher.listen(UserRegistered, lambda e: sink.append(f"fn:{e.user_id}"))
    dispatcher.dispatch(UserRegistered("u1"))
    assert sink == ["u1", "fn:u1"]


def test_stop_propagation_skips_remaining() -> None:
    sink: list[str] = []
    dispatcher = EventDispatcher()

    def stopper(event: UserRegistered) -> None:
        sink.append("a")
        event.stop()

    dispatcher.listen(UserRegistered, stopper)
    dispatcher.listen(UserRegistered, lambda e: sink.append("b"))
    dispatcher.dispatch(UserRegistered("u1"))
    assert sink == ["a"]


def test_dispatch_until_returns_first_value() -> None:
    dispatcher = EventDispatcher()
    dispatcher.listen(UserRegistered, lambda e: None)
    dispatcher.listen(UserRegistered, lambda e: f"ok-{e.user_id}")
    dispatcher.listen(UserRegistered, lambda e: "late")
    result = dispatcher.dispatch_until(UserRegistered("u9"))
    assert result == "ok-u9"


def test_forget_and_wildcard() -> None:
    sink: list[str] = []
    dispatcher = EventDispatcher()
    dispatcher.listen(UserRegistered, lambda e: sink.append("typed"))
    dispatcher.listen("*", lambda e: sink.append("wild"))
    dispatcher.dispatch(UserRegistered("x"))
    assert sink == ["typed", "wild"]
    dispatcher.forget(UserRegistered)
    sink.clear()
    dispatcher.dispatch(UserRegistered("y"))
    assert sink == ["wild"]


def test_listener_exception_propagates() -> None:
    dispatcher = EventDispatcher()

    def boom(event: Event) -> None:
        raise RuntimeError("nope")

    dispatcher.listen(UserRegistered, boom)
    with pytest.raises(RuntimeError, match="nope"):
        dispatcher.dispatch(UserRegistered("z"))


def test_default_singleton() -> None:
    a = event_dispatcher()
    b = event_dispatcher()
    assert a is b
