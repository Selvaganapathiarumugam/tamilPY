from typing import Any


class Response:
    """
    Lightweight response helper for JSON/API payloads.
    """

    def __init__(
        self,
        data: Any = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.data = data
        self.status_code = status_code
        self.headers = headers or {}

    @classmethod
    def json(
        cls,
        data: Any,
        status_code: int = 200,
    ) -> "Response":
        """Create a JSON response."""
        return cls(data=data, status_code=status_code)

    @classmethod
    def error(
        cls,
        message: str,
        status_code: int = 400,
    ) -> "Response":
        """Create an error response payload."""
        return cls(
            data={"error": message},
            status_code=status_code,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the response envelope."""
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "data": self.data,
        }
