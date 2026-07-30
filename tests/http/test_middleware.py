"""Tests for middleware groups."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from tpy.http import HttpError, Middleware, MiddlewareManager, RequestIdMiddleware
from tpy.http.middleware import CallNext
from tpy.kernel import Application


class AddHeaderMiddleware(Middleware):
    async def handle(self, request: Request, call_next: CallNext):
        response = await call_next(request)
        response.headers["X-Demo"] = "1"
        return response


def test_group_resolve_and_unknown():
    mw = MiddlewareManager()
    mw.register("request_id", RequestIdMiddleware)
    mw.group("api", ["request_id"])
    assert mw.resolve("api") == [RequestIdMiddleware]
    with pytest.raises(HttpError):
        mw.resolve("missing")
    with pytest.raises(HttpError):
        mw.group("broken", ["nope"]).resolve("broken")


def test_apply_middleware_group_on_fastapi():
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    mw = MiddlewareManager()
    mw.register("demo", AddHeaderMiddleware)
    mw.register("request_id", RequestIdMiddleware)
    mw.group("api", ["demo", "request_id"])
    mw.apply(app, "api")

    client = TestClient(app)
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.headers.get("X-Demo") == "1"
    assert "X-Request-ID" in response.headers


def test_application_middleware_groups(tmp_path: Path):
    kernel = Application(tmp_path)
    kernel.middleware.register("demo", AddHeaderMiddleware)
    kernel.middleware.append("api", "demo")
    api = kernel.middleware_groups("api").create(title="MW")

    @api.get("/x")
    def x():
        return {"ok": True}

    client = TestClient(api)
    response = client.get("/x")
    assert response.headers.get("X-Demo") == "1"
    assert "X-Request-ID" in response.headers
