"""FastAPI application factory for ``tpy studio``."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from tpy.studio import studio_version
from tpy.studio.api import create_api_router


def ui_dist_dir() -> Path:
    """Path to the pre-built Studio SPA (``ui/dist``)."""
    return Path(__file__).resolve().parent / "ui" / "dist"


def create_app(project_root: Path | str = ".") -> FastAPI:
    """
    Create the Studio FastAPI app for ``project_root``.

    Serves ``/api/studio/*`` and the static UI from ``ui/dist`` when built.
    """
    root = Path(project_root).resolve()
    app = FastAPI(
        title="tamilPY Studio",
        version=studio_version(),
        docs_url="/api/docs",
        redoc_url=None,
    )
    app.state.project_root = root
    app.include_router(create_api_router(root))

    dist = ui_dist_dir()
    if dist.exists():
        assets = dist / "assets"
        if assets.exists():
            app.mount(
                "/assets",
                StaticFiles(directory=assets),
                name="studio-assets",
            )

        @app.get("/")
        async def spa_index() -> FileResponse:
            return FileResponse(dist / "index.html")

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str) -> FileResponse:
            candidate = dist / full_path
            if candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")
    else:

        @app.get("/")
        async def missing_ui() -> dict:
            return {
                "error": "Studio UI not built",
                "hint": (
                    "Run: cd tpy/studio/ui && npm install && npm run build"
                ),
                "version": studio_version(),
            }

    return app
