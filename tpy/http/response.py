"""
Consistent JSON API response helpers for FastAPI apps.
"""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse, Response


class ApiResponse:
    """
    Factory for uniform JSON API envelopes.

    Success shape::

        {"success": true, "message": ..., "data": ..., "meta": ...}

    Error shape::

        {"success": false, "message": ..., "errors": ..., "data": null}
    """

    @staticmethod
    def payload(
        *,
        success: bool,
        data: Any = None,
        message: str | None = None,
        meta: dict[str, Any] | None = None,
        errors: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        """Build the envelope dict without wrapping in ``JSONResponse``."""
        body: dict[str, Any] = {
            "success": success,
            "message": message,
            "data": data,
        }
        if success:
            body["meta"] = meta
        else:
            body["errors"] = errors or {}
            body["data"] = None if data is None else data
        return body

    @classmethod
    def json(
        cls,
        data: Any = None,
        *,
        success: bool = True,
        message: str | None = None,
        meta: dict[str, Any] | None = None,
        errors: dict[str, Any] | list[Any] | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """Return a ``JSONResponse`` with the standard envelope."""
        body = cls.payload(
            success=success,
            data=data,
            message=message,
            meta=meta,
            errors=errors,
        )
        return JSONResponse(
            content=body,
            status_code=status_code,
            headers=headers,
        )

    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str | None = None,
        *,
        meta: dict[str, Any] | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """200 (or custom) success response."""
        return cls.json(
            data,
            success=True,
            message=message,
            meta=meta,
            status_code=status_code,
            headers=headers,
        )

    @classmethod
    def created(
        cls,
        data: Any = None,
        message: str | None = "Created",
        *,
        meta: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """201 Created success response."""
        return cls.success(
            data,
            message=message,
            meta=meta,
            status_code=201,
            headers=headers,
        )

    @classmethod
    def paginated(
        cls,
        paginator: Any,
        message: str | None = None,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """
        Success response from a paginator.

        Accepts ``LengthAwarePaginator`` (``to_dict()``) or a dict with
        ``data`` / ``meta`` keys.
        """
        if hasattr(paginator, "to_dict"):
            envelope = paginator.to_dict()
        elif isinstance(paginator, dict):
            envelope = paginator
        else:
            raise TypeError(
                "paginated() expects LengthAwarePaginator or dict with data/meta"
            )
        return cls.success(
            envelope.get("data"),
            message=message,
            meta=envelope.get("meta"),
            status_code=status_code,
            headers=headers,
        )

    @classmethod
    def error(
        cls,
        message: str,
        *,
        status_code: int = 400,
        errors: dict[str, Any] | list[Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """Error response with optional field ``errors``."""
        return cls.json(
            data,
            success=False,
            message=message,
            errors=errors,
            status_code=status_code,
            headers=headers,
        )

    @classmethod
    def validation_error(
        cls,
        errors: dict[str, Any] | list[Any],
        message: str = "Validation failed",
        *,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """
        422 validation error response.

        Accepts ``dict[str, str]``, ``dict[str, list[str]]``, or a
        ``ValidationException``-style mapping.
        """
        if hasattr(errors, "first_messages"):
            errors = errors.first_messages()  # type: ignore[assignment]
        elif isinstance(errors, dict):
            normalized: dict[str, Any] = {}
            for key, value in errors.items():
                if isinstance(value, list):
                    normalized[key] = value[0] if value else "Invalid"
                else:
                    normalized[key] = value
            errors = normalized
        return cls.error(
            message,
            status_code=422,
            errors=errors,
            headers=headers,
        )

    @classmethod
    def not_found(
        cls,
        message: str = "Not found",
        *,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """404 Not Found."""
        return cls.error(message, status_code=404, headers=headers)

    @classmethod
    def unauthorized(
        cls,
        message: str = "Unauthorized",
        *,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """401 Unauthorized."""
        return cls.error(message, status_code=401, headers=headers)

    @classmethod
    def forbidden(
        cls,
        message: str = "Forbidden",
        *,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """403 Forbidden."""
        return cls.error(message, status_code=403, headers=headers)

    @classmethod
    def no_content(cls, headers: dict[str, str] | None = None) -> Response:
        """204 No Content (empty body)."""
        return Response(status_code=204, headers=headers)
