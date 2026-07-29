"""Tests for ApiResponse helpers."""

from __future__ import annotations

import json

from fastapi.responses import JSONResponse, Response

from tpy.http import ApiResponse
from tpy.query.paginator import LengthAwarePaginator
from tpy.runtime.response import Response as RuntimeResponse


def _body(response: JSONResponse) -> dict:
    return json.loads(response.body.decode("utf-8"))


def test_success_envelope():
    response = ApiResponse.success({"id": 1}, message="ok")
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    body = _body(response)
    assert body["success"] is True
    assert body["message"] == "ok"
    assert body["data"] == {"id": 1}
    assert body["meta"] is None


def test_created_and_errors():
    created = ApiResponse.created({"id": 2})
    assert created.status_code == 201
    assert _body(created)["message"] == "Created"

    err = ApiResponse.validation_error({"email": "required"})
    assert err.status_code == 422
    body = _body(err)
    assert body["success"] is False
    assert body["errors"] == {"email": "required"}
    assert body["data"] is None


def test_helpers_status_codes():
    assert ApiResponse.not_found().status_code == 404
    assert ApiResponse.unauthorized().status_code == 401
    assert ApiResponse.forbidden().status_code == 403
    empty = ApiResponse.no_content()
    assert isinstance(empty, Response)
    assert empty.status_code == 204


def test_paginated_from_paginator():
    page = LengthAwarePaginator(
        items=[{"id": 1}],
        total=10,
        page=1,
        per_page=1,
    )
    response = ApiResponse.paginated(page)
    body = _body(response)
    assert body["data"] == [{"id": 1}]
    assert body["meta"]["total"] == 10
    assert body["meta"]["last_page"] == 10


def test_runtime_response_success_soft_break():
    legacy = RuntimeResponse.success({"a": 1}, message="hi")
    assert legacy.status_code == 200
    assert legacy.data["success"] is True
    assert legacy.data["data"] == {"a": 1}
    fastapi_response = legacy.to_fastapi()
    assert isinstance(fastapi_response, JSONResponse)
