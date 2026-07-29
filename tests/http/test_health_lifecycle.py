"""Tests for health checks and lifecycle hooks."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from tpy.http import (
    DiskSpaceCheck,
    HealthChecker,
    Lifecycle,
    attach_lifecycle,
    register_health_routes,
)
from tpy.kernel import Application


def test_health_checker_ok_and_error():
    health = HealthChecker()
    health.add("app", lambda: True)
    health.add("boom", lambda: (_ for _ in ()).throw(RuntimeError("down")))
    report = health.run()
    assert report.status == "degraded"
    assert report.checks["app"].status == "ok"
    assert report.checks["boom"].status == "error"


def test_disk_space_check(tmp_path: Path):
    check = DiskSpaceCheck(tmp_path, min_free_mb=1)
    result = check()
    assert result["status"] == "ok"
    assert "free_mb" in result


def test_register_health_routes():
    app = FastAPI()
    health = HealthChecker()
    health.add("db", lambda: False)
    register_health_routes(app, health)

    client = TestClient(app)
    live = client.get("/health")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"

    ready = client.get("/health/ready")
    assert ready.status_code == 503
    assert ready.json()["status"] == "degraded"


def test_lifecycle_before_after_and_exception():
    app = FastAPI()
    life = Lifecycle()
    seen: list[str] = []

    @life.before_request
    def before(request):
        seen.append("before")

    @life.after_request
    def after(request, response):
        seen.append("after")
        response.headers["X-Life"] = "1"
        return response

    @life.on_exception
    def on_exc(request, exc):
        seen.append("exc")
        return JSONResponse({"error": str(exc)}, status_code=400)

    attach_lifecycle(app, life)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/bad")
    def bad():
        raise RuntimeError("nope")

    with TestClient(app) as client:
        response = client.get("/ok")
        assert response.status_code == 200
        assert response.headers.get("X-Life") == "1"
        assert "before" in seen and "after" in seen

        bad_response = client.get("/bad")
        assert bad_response.status_code == 400
        assert "exc" in seen


def test_application_wires_health_and_lifecycle(tmp_path: Path):
    kernel = Application(tmp_path)
    booted: list[str] = []

    @kernel.lifecycle.on_boot
    def boot():
        booted.append("boot")

    kernel.health.add("custom", lambda: {"status": "ok", "message": "fine"})
    api = kernel.create(title="HealthApp")

    @api.get("/ping")
    def ping():
        return {"pong": True}

    with TestClient(api) as client:
        assert booted == ["boot"]
        assert client.get("/health").json()["status"] == "ok"
        ready = client.get("/health/ready")
        assert ready.status_code == 200
        assert "custom" in ready.json()["checks"]
        assert client.get("/ping").status_code == 200
