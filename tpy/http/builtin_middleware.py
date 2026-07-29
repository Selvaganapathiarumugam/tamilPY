"""
Built-in HTTP middleware examples.
"""

from __future__ import annotations

import uuid
from typing import Any

from starlette.requests import Request

from tpy.http.middleware import CallNext, Middleware


class RequestIdMiddleware(Middleware):
    """Attach ``X-Request-ID`` to request state and response headers."""

    header_name = "X-Request-ID"

    async def handle(self, request: Request, call_next: CallNext) -> Any:
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response
