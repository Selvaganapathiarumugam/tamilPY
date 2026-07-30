"""
Request / application lifecycle hooks.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from tpy.http.middleware import CallNext, Middleware, _MiddlewareBridge

Hook = Callable[..., Any]


class Lifecycle:
    """
    Sync/async lifecycle hooks for the application and HTTP requests.

    Hooks:
    - ``on_boot`` / ``on_shutdown`` — app process lifespan
    - ``before_request`` / ``after_request`` — per HTTP request
    - ``on_exception`` — when a request handler raises
    """

    def __init__(self) -> None:
        self._hooks: dict[str, list[Hook]] = defaultdict(list)

    def on_boot(self, callback: Hook) -> Hook:
        """Register a boot/startup hook (also usable as decorator)."""
        self._hooks["boot"].append(callback)
        return callback

    def on_shutdown(self, callback: Hook) -> Hook:
        """Register a shutdown hook."""
        self._hooks["shutdown"].append(callback)
        return callback

    def before_request(self, callback: Hook) -> Hook:
        """Register a before-request hook ``(request) -> None``."""
        self._hooks["before_request"].append(callback)
        return callback

    def after_request(self, callback: Hook) -> Hook:
        """Register an after-request hook ``(request, response) -> response``."""
        self._hooks["after_request"].append(callback)
        return callback

    def on_exception(self, callback: Hook) -> Hook:
        """Register ``(request, exc) -> response|None``."""
        self._hooks["exception"].append(callback)
        return callback

    def clear(self, event: str | None = None) -> None:
        """Clear hooks for ``event`` or all events."""
        if event is None:
            self._hooks.clear()
        else:
            self._hooks.pop(event, None)

    def listeners(self, event: str) -> list[Hook]:
        """Return hooks for ``event``."""
        return list(self._hooks.get(event, []))

    async def run_boot(self) -> None:
        """Run boot hooks."""
        await self._run_list(self._hooks.get("boot", []))

    async def run_shutdown(self) -> None:
        """Run shutdown hooks."""
        await self._run_list(self._hooks.get("shutdown", []))

    async def run_before_request(self, request: Request) -> None:
        """Run before-request hooks."""
        for hook in self._hooks.get("before_request", []):
            result = hook(request)
            if hasattr(result, "__await__"):
                await result

    async def run_after_request(
        self,
        request: Request,
        response: Response,
    ) -> Response:
        """Run after-request hooks; each may replace the response."""
        current = response
        for hook in self._hooks.get("after_request", []):
            result = hook(request, current)
            if hasattr(result, "__await__"):
                result = await result
            if result is not None:
                current = result
        return current

    async def run_exception(
        self,
        request: Request,
        exc: BaseException,
    ) -> Response | None:
        """Run exception hooks until one returns a Response."""
        for hook in self._hooks.get("exception", []):
            result = hook(request, exc)
            if hasattr(result, "__await__"):
                result = await result
            if result is not None:
                return result
        return None

    async def _run_list(self, hooks: list[Hook]) -> None:
        for hook in hooks:
            result = hook()
            if hasattr(result, "__await__"):
                await result


class LifecycleMiddleware(Middleware):
    """
    HTTP middleware that executes lifecycle request hooks.

    Reads ``request.app.state.lifecycle`` (set by ``attach_lifecycle``).
    """

    async def handle(self, request: Request, call_next: CallNext) -> Any:
        lifecycle = getattr(
            getattr(request.app, "state", None), "lifecycle", None
        )
        if lifecycle is None:
            return await call_next(request)

        await lifecycle.run_before_request(request)
        try:
            response = await call_next(request)
        except Exception as exc:
            handled = await lifecycle.run_exception(request, exc)
            if handled is not None:
                return handled
            raise
        return await lifecycle.run_after_request(request, response)


def attach_lifecycle(app: Any, lifecycle: Lifecycle) -> Lifecycle:
    """
    Wire lifespan + request middleware for ``lifecycle`` onto a FastAPI app.
    """
    state = getattr(app, "state", None)
    if state is not None:
        state.lifecycle = lifecycle

    previous = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(fastapi_app: Any) -> AsyncIterator[None]:
        await lifecycle.run_boot()
        try:
            async with previous(fastapi_app):
                yield
        finally:
            await lifecycle.run_shutdown()

    app.router.lifespan_context = lifespan
    app.add_middleware(_MiddlewareBridge, middleware_cls=LifecycleMiddleware)
    return lifecycle
