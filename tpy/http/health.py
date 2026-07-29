"""
Health check registry and FastAPI route helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

CheckCallable = Callable[[], Any]


@dataclass(slots=True)
class HealthCheckResult:
    """Outcome of a single named check."""

    name: str
    status: str  # ok | error
    message: str = "ok"
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "status": self.status,
            "message": self.message,
        }
        if self.meta:
            payload["meta"] = self.meta
        return payload


@dataclass(slots=True)
class HealthReport:
    """Aggregate health report."""

    status: str  # ok | degraded | error
    checks: dict[str, HealthCheckResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "checks": {
                name: result.to_dict() for name, result in self.checks.items()
            },
        }

    @property
    def ok(self) -> bool:
        return self.status == "ok"


class HealthChecker:
    """
    Register and run named health checks.

    Example::

        health = HealthChecker()
        health.add("app", lambda: True)
        health.add("disk", DiskSpaceCheck("."))
        report = health.run()
    """

    def __init__(self) -> None:
        self._checks: dict[str, CheckCallable] = {}

    def add(self, name: str, check: CheckCallable) -> HealthChecker:
        """Register ``check`` under ``name``."""
        self._checks[name] = check
        return self

    def remove(self, name: str) -> None:
        """Remove a registered check."""
        self._checks.pop(name, None)

    def names(self) -> list[str]:
        """Return registered check names."""
        return list(self._checks)

    def run(self, *only: str) -> HealthReport:
        """
        Execute checks and return an aggregate report.

        Args:
            only: Optional subset of check names; default runs all.
        """
        selected = only or tuple(self._checks)
        results: dict[str, HealthCheckResult] = {}
        for name in selected:
            check = self._checks.get(name)
            if check is None:
                results[name] = HealthCheckResult(
                    name=name,
                    status="error",
                    message=f"Unknown check: {name}",
                )
                continue
            try:
                outcome = check()
                results[name] = self._normalize(name, outcome)
            except Exception as error:  # noqa: BLE001 — report as check failure
                results[name] = HealthCheckResult(
                    name=name,
                    status="error",
                    message=str(error) or error.__class__.__name__,
                )

        statuses = {item.status for item in results.values()}
        if not results or statuses == {"ok"}:
            overall = "ok"
        elif "ok" in statuses:
            overall = "degraded"
        else:
            overall = "error"
        return HealthReport(status=overall, checks=results)

    def _normalize(self, name: str, outcome: Any) -> HealthCheckResult:
        if isinstance(outcome, HealthCheckResult):
            return outcome
        if outcome is True or outcome is None:
            return HealthCheckResult(name=name, status="ok")
        if outcome is False:
            return HealthCheckResult(
                name=name, status="error", message="check returned false"
            )
        if isinstance(outcome, str):
            return HealthCheckResult(name=name, status="ok", message=outcome)
        if isinstance(outcome, dict):
            status = str(outcome.get("status", "ok"))
            message = str(outcome.get("message", "ok"))
            meta = {
                key: value
                for key, value in outcome.items()
                if key not in {"status", "message"}
            }
            return HealthCheckResult(
                name=name, status=status, message=message, meta=meta
            )
        return HealthCheckResult(name=name, status="ok", message=str(outcome))


class DiskSpaceCheck:
    """Fail when free disk space is below ``min_free_mb``."""

    def __init__(self, path: Path | str = ".", min_free_mb: int = 100) -> None:
        self.path = Path(path)
        self.min_free_mb = min_free_mb

    def __call__(self) -> dict[str, Any]:
        import shutil

        usage = shutil.disk_usage(self.path)
        free_mb = usage.free // (1024 * 1024)
        ok = free_mb >= self.min_free_mb
        return {
            "status": "ok" if ok else "error",
            "message": f"{free_mb}MB free",
            "free_mb": free_mb,
            "min_free_mb": self.min_free_mb,
        }


def register_health_routes(
    app: Any,
    checker: HealthChecker | None = None,
    *,
    prefix: str = "",
    liveness_path: str = "/health",
    readiness_path: str = "/health/ready",
) -> HealthChecker:
    """
    Mount liveness + readiness endpoints on a FastAPI app.

    - ``GET /health`` — process up (always 200)
    - ``GET /health/ready`` — runs checks; 503 when not ok
    """
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

    health = checker or HealthChecker()
    if "app" not in health.names():
        health.add("app", lambda: True)

    router = APIRouter(tags=["health"])

    @router.get(liveness_path)
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @router.get(readiness_path)
    def ready() -> JSONResponse:
        report = health.run()
        code = 200 if report.ok else 503
        return JSONResponse(report.to_dict(), status_code=code)

    app.include_router(router, prefix=prefix.rstrip("/"))
    return health
