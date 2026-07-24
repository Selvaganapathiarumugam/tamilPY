from typing import Any


class Request:
    """
    Lightweight request wrapper used by generated controllers.
    """

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        headers: dict[str, str] | None = None,
        query: dict[str, Any] | None = None,
        body: Any = None,
    ) -> None:
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.query = query or {}
        self.body = body

    def get_header(self, name: str, default: str | None = None) -> str | None:
        """Return a header value by name (case-insensitive)."""
        target = name.lower()
        for key, value in self.headers.items():
            if key.lower() == target:
                return value
        return default

    def input(self, key: str, default: Any = None) -> Any:
        """Return a value from the body dict or query string."""
        if isinstance(self.body, dict) and key in self.body:
            return self.body[key]
        return self.query.get(key, default)
