from typing import Any


class Response:
    """
    Lightweight response helper for JSON/API payloads.

    Prefer ``tpy.http.ApiResponse`` for FastAPI ``JSONResponse`` envelopes
    in application controllers. This class remains for simple dict payloads
    and backward compatibility.
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

    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str | None = None,
        status_code: int = 200,
    ) -> "Response":
        """
        Create a success envelope (dict-only).

        For FastAPI responses use ``tpy.http.ApiResponse.success``.
        """
        from tpy.http import ApiResponse

        return cls(
            data=ApiResponse.payload(
                success=True,
                data=data,
                message=message,
            ),
            status_code=status_code,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the response envelope."""
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "data": self.data,
        }

    def to_fastapi(self):
        """Convert to FastAPI ``JSONResponse`` via ``ApiResponse``."""
        from fastapi.responses import JSONResponse

        return JSONResponse(
            content=self.data,
            status_code=self.status_code,
            headers=self.headers or None,
        )
