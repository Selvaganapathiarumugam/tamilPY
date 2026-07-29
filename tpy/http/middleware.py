"""
Named middleware and middleware groups for FastAPI apps.
"""

from __future__ import annotations

from abc import ABC
from typing import Any, Awaitable, Callable, Sequence

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from tpy.http.exceptions import HttpError

CallNext = Callable[[Request], Awaitable[Response]]


class Middleware(ABC):
    """
    Sync-friendly HTTP middleware.

    Implement ``handle`` to inspect/modify the request and response.
    The default bridge runs ``handle`` inside Starlette's
    ``BaseHTTPMiddleware``.
    """

    def handle(self, request: Request, call_next: CallNext) -> Any:
        """
        Process ``request``.

        May be sync or async. Call ``await call_next(request)`` (or return
        an awaitable from a sync function that the bridge awaits).
        Prefer async ``handle`` for I/O.
        """
        return call_next(request)


class _MiddlewareBridge(BaseHTTPMiddleware):
    """Adapt a ``Middleware`` subclass to Starlette."""

    def __init__(self, app: ASGIApp, middleware_cls: type[Middleware]) -> None:
        super().__init__(app)
        self.middleware_cls = middleware_cls

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        instance = self.middleware_cls()
        result = instance.handle(request, call_next)
        if hasattr(result, "__await__"):
            return await result  # type: ignore[misc]
        return result  # type: ignore[return-value]


class MiddlewareManager:
    """
    Registry of named middleware and named groups (Laravel-style).

    Example::

        mw = MiddlewareManager()
        mw.register("request_id", RequestIdMiddleware)
        mw.group("api", ["request_id"])
        mw.apply(fastapi_app, "api")
    """

    def __init__(self) -> None:
        self._aliases: dict[str, type[Middleware] | type] = {}
        self._groups: dict[str, list[str]] = {
            "api": [],
            "web": [],
            "auth": [],
        }

    def register(
        self,
        name: str,
        middleware: type[Middleware] | type,
    ) -> MiddlewareManager:
        """Register a middleware class under ``name``."""
        self._aliases[name] = middleware
        return self

    def group(
        self,
        name: str,
        middleware: Sequence[str] | None = None,
        *,
        append: bool = False,
    ) -> MiddlewareManager:
        """
        Define or replace a middleware group.

        Args:
            name: Group name (e.g. ``api``).
            middleware: Ordered alias list.
            append: When True, append to an existing group instead of replace.
        """
        names = list(middleware or [])
        if append and name in self._groups:
            self._groups[name] = list(self._groups[name]) + names
        else:
            self._groups[name] = names
        return self

    def append(self, group: str, *middleware_names: str) -> MiddlewareManager:
        """Append middleware aliases to an existing group."""
        return self.group(group, middleware_names, append=True)

    def has(self, name: str) -> bool:
        """Return whether a middleware alias exists."""
        return name in self._aliases

    def has_group(self, name: str) -> bool:
        """Return whether a group name exists."""
        return name in self._groups

    def resolve(self, group: str) -> list[type]:
        """
        Expand a group into ordered middleware classes.

        Raises:
            HttpError: Unknown group or alias.
        """
        if group not in self._groups:
            raise HttpError(f"Unknown middleware group: {group}")
        resolved: list[type] = []
        for alias in self._groups[group]:
            if alias not in self._aliases:
                raise HttpError(
                    f"Unknown middleware '{alias}' in group '{group}'"
                )
            resolved.append(self._aliases[alias])
        return resolved

    def apply(self, app: Any, *groups: str) -> Any:
        """
        Attach middleware from ``groups`` onto a FastAPI/Starlette app.

        Starlette applies middleware in reverse add order; this method adds
        group middleware so the first alias in the group runs first.
        """
        classes: list[type] = []
        for group in groups:
            classes.extend(self.resolve(group))

        # add_middleware wraps outward — reverse so first listed runs first
        for middleware_cls in reversed(classes):
            if issubclass(middleware_cls, Middleware):
                app.add_middleware(_MiddlewareBridge, middleware_cls=middleware_cls)
            else:
                app.add_middleware(middleware_cls)
        return app

    @property
    def groups(self) -> dict[str, list[str]]:
        """Copy of defined groups."""
        return {key: list(value) for key, value in self._groups.items()}

    @property
    def aliases(self) -> dict[str, type]:
        """Copy of middleware aliases."""
        return dict(self._aliases)
