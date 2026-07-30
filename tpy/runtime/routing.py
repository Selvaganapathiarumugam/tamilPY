from collections.abc import Callable
from typing import Any


class Route:
    """
    A single HTTP route definition.
    """

    def __init__(
        self,
        method: str,
        path: str,
        handler: Callable[..., Any],
        name: str | None = None,
    ) -> None:
        self.method = method.upper()
        self.path = path
        self.handler = handler
        self.name = name or handler.__name__


class Router:
    """
    Simple in-memory router used by the TPY runtime.
    """

    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix.rstrip("/")
        self.routes: list[Route] = []

    def add(
        self,
        method: str,
        path: str,
        handler: Callable[..., Any],
        name: str | None = None,
    ) -> Route:
        """Register a route and return it."""
        full_path = f"{self.prefix}{path}"
        route = Route(method, full_path, handler, name)
        self.routes.append(route)
        return route

    def get(
        self, path: str, handler: Callable[..., Any], name: str | None = None
    ) -> Route:
        """Register a GET route."""
        return self.add("GET", path, handler, name)

    def post(
        self, path: str, handler: Callable[..., Any], name: str | None = None
    ) -> Route:
        """Register a POST route."""
        return self.add("POST", path, handler, name)

    def put(
        self, path: str, handler: Callable[..., Any], name: str | None = None
    ) -> Route:
        """Register a PUT route."""
        return self.add("PUT", path, handler, name)

    def delete(
        self, path: str, handler: Callable[..., Any], name: str | None = None
    ) -> Route:
        """Register a DELETE route."""
        return self.add("DELETE", path, handler, name)

    def match(self, method: str, path: str) -> Route | None:
        """
        Find a route for the given method and path.

        Note:
            Exact path matching only. Path parameters are handled by FastAPI
            in generated applications.
        """
        method = method.upper()
        for route in self.routes:
            if route.method == method and route.path == path:
                return route
        return None
