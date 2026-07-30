"""Studio REST API under ``/api/studio``."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from tpy.generator.auth_generator import AuthGenerator
from tpy.schema import (
    from_json,
    parse_file,
    serialize,
    to_json,
    validate_program,
)
from tpy.starter_templates import (
    apply_template_files,
    get_template,
    list_templates,
    read_schema,
)
from tpy.studio import studio_version
from tpy.studio.auth_store import load_auth, save_auth
from tpy.studio.env_config import (
    build_database_url,
    database_public_config,
    write_env,
)
from tpy.studio.runners import stream_command
from tpy.utils.file_manager import FileManager


class SchemaBody(BaseModel):
    """Proposed schema AST from the Studio UI."""

    database: str | None = None
    models: list[dict[str, Any]] = Field(default_factory=list)
    enums: list[dict[str, Any]] = Field(default_factory=list)
    auth: dict[str, Any] | None = None


class ConfirmBody(BaseModel):
    confirm: bool = False


class SeedBody(BaseModel):
    fake: bool = False
    count: int | None = None
    model: str | None = None


class DatabaseBody(BaseModel):
    provider: str = "sqlite"
    database_url: str | None = None
    path: str | None = None
    host: str | None = None
    port: str | None = None
    database_name: str | None = None
    username: str | None = None
    password: str | None = None
    dry_run: bool = False


class AuthBody(BaseModel):
    enabled: bool | None = None
    roles: list[str] | None = None
    bootstrap_email: str | None = None
    bootstrap_password: str | None = None


class TemplateApplyBody(BaseModel):
    name: str
    confirm: bool = False


def create_api_router(project_root: Path) -> APIRouter:
    """Build the Studio API router bound to ``project_root``."""
    router = APIRouter(prefix="/api/studio", tags=["studio"])
    root = Path(project_root)

    def schema_path() -> Path:
        return root / "schema.tpy"

    def load_program():
        path = schema_path()
        if not path.exists():
            raise HTTPException(404, "schema.tpy not found")
        return parse_file(path)

    def schema_payload() -> dict[str, Any]:
        program = load_program()
        payload = to_json(program)
        payload["auth"] = load_auth(root)
        return payload

    def program_from_body(body: SchemaBody):
        data = body.model_dump()
        data.pop("auth", None)
        return from_json(data)

    @router.get("/health")
    def health() -> dict[str, Any]:
        dist = Path(__file__).resolve().parent / "ui" / "dist" / "index.html"
        return {
            "ok": True,
            "version": studio_version(),
            "project_root": str(root.resolve()),
            "ui_built": dist.exists(),
            "schema_exists": schema_path().exists(),
        }

    @router.get("/schema")
    def get_schema() -> dict[str, Any]:
        return schema_payload()

    @router.post("/schema/preview")
    def preview_schema(body: SchemaBody) -> dict[str, Any]:
        path = schema_path()
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        program = program_from_body(body)
        diagnostics = validate_program(program, filename="schema.tpy")
        new = serialize(program)
        diff = "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile="schema.tpy",
                tofile="schema.tpy (proposed)",
            )
        )
        return {
            "diff": diff,
            "diagnostics": [
                {
                    "line": d.line,
                    "message": d.message,
                    "severity": d.severity,
                    "hint": d.hint,
                    "formatted": d.format(),
                }
                for d in diagnostics
            ],
            "proposed": new,
        }

    @router.post("/schema/save")
    def save_schema(body: SchemaBody) -> dict[str, Any]:
        program = program_from_body(body)
        validate_program(program, filename="schema.tpy", raise_on_error=True)
        FileManager.write(schema_path(), serialize(program))
        if body.auth is not None:
            save_auth(root, body.auth)
        return schema_payload()

    @router.get("/database")
    def get_database() -> dict[str, Any]:
        return database_public_config(root)

    @router.post("/database")
    def post_database(body: DatabaseBody) -> dict[str, Any]:
        try:
            provider, url = build_database_url(body.model_dump())
        except ValueError as error:
            raise HTTPException(400, str(error)) from error

        if body.dry_run:
            return _test_connection(root, provider, url, persist=False)

        write_env(
            root,
            {
                "TPY_DATABASE": provider,
                "DATABASE_URL": url,
            },
        )
        if schema_path().exists():
            program = load_program()
            from tpy.parser.ast import DatabaseNode

            program.database = DatabaseNode(provider=provider)
            FileManager.write(schema_path(), serialize(program))
        result = _test_connection(root, provider, url, persist=True)
        result["saved"] = True
        return result

    @router.get("/auth")
    def get_auth() -> dict[str, Any]:
        return load_auth(root)

    @router.post("/auth")
    def post_auth(body: AuthBody) -> dict[str, Any]:
        public = save_auth(root, body.model_dump(exclude_unset=True))
        if body.enabled is True and not (root / ".tpy_auth").exists():
            try:
                AuthGenerator(root).generate()
            except Exception as error:
                raise HTTPException(400, f"Failed to enable auth: {error}") from error
            public = load_auth(root)
            public["enabled"] = True
        return public

    @router.post("/build")
    async def post_build() -> StreamingResponse:
        return StreamingResponse(
            stream_command(["build", "--skip-db"], cwd=root),
            media_type="text/event-stream",
        )

    @router.post("/migrate")
    async def post_migrate() -> StreamingResponse:
        return StreamingResponse(
            stream_command(["migrate"], cwd=root),
            media_type="text/event-stream",
        )

    @router.post("/migrate/rollback")
    async def post_rollback(body: ConfirmBody) -> StreamingResponse:
        if not body.confirm:
            raise HTTPException(400, 'Body must include {"confirm": true}')
        return StreamingResponse(
            stream_command(["migrate", "rollback"], cwd=root),
            media_type="text/event-stream",
        )

    @router.post("/seed")
    async def post_seed(body: SeedBody | None = None) -> StreamingResponse:
        # Avoid calling SeedBody() at import time (flake8-bugbear B008)
        body = body or SeedBody()
        args = ["seed"]
        # fake flags reserved for Part 3.2 — ignored safely for now
        _ = body
        return StreamingResponse(
            stream_command(args, cwd=root),
            media_type="text/event-stream",
        )

    @router.post("/serve")
    async def post_serve() -> StreamingResponse:
        return StreamingResponse(
            stream_command(["serve"], cwd=root),
            media_type="text/event-stream",
        )

    @router.get("/routes")
    def get_routes() -> dict[str, Any]:
        try:
            from tpy.http.route_cache import RouteCache

            cache = RouteCache(root)
            routes = cache.load()
            if not routes:
                try:
                    import importlib
                    import sys

                    sys.path.insert(0, str(root))
                    module = importlib.import_module("app.main")
                    # use attribute access to avoid flake8-bugbear B009
                    try:
                        app = module.app
                    except AttributeError:
                        # missing attribute -> fall back to empty routes as before
                        raise
                    routes = RouteCache.collect(app)
                except Exception:
                    routes = []
            return {"routes": routes}
        except Exception as error:
            return {"routes": [], "error": str(error)}

    @router.get("/templates")
    def get_templates() -> dict[str, Any]:
        return {
            "templates": [
                {
                    "name": t.name,
                    "description": t.description,
                    "models": t.models,
                }
                for t in list_templates()
            ]
        }

    @router.post("/templates/apply")
    def apply_template(body: TemplateApplyBody) -> dict[str, Any]:
        try:
            info = get_template(body.name)
        except KeyError as error:
            raise HTTPException(404, str(error)) from error

        proposed = read_schema(body.name)
        old = (
            schema_path().read_text(encoding="utf-8")
            if schema_path().exists()
            else ""
        )
        diff = "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                proposed.splitlines(keepends=True),
                fromfile="schema.tpy",
                tofile=f"template:{body.name}",
            )
        )
        if not body.confirm:
            return {
                "preview": True,
                "diff": diff,
                "template": info.name,
                "models": info.models,
            }
        apply_template_files(root, body.name)
        return {
            "preview": False,
            "applied": True,
            "schema": schema_payload(),
            "diff": diff,
        }

    return router


def _test_connection(
    root: Path,
    provider: str,
    url: str,
    *,
    persist: bool,
) -> dict[str, Any]:
    previous = None
    env_path = root / ".env"
    if not persist and env_path.exists():
        previous = env_path.read_text(encoding="utf-8")
    write_env(root, {"TPY_DATABASE": provider, "DATABASE_URL": url})
    try:
        from tpy.providers.factory import get_provider

        db = get_provider(project_root=root)
        db.connect()
        db.close()
        ok = True
        error = None
    except Exception as exc:
        ok = False
        error = str(exc)
    if not persist and previous is not None:
        env_path.write_text(previous, encoding="utf-8")
    elif not persist and previous is None and env_path.exists():
        env_path.unlink()
    return {
        "ok": ok,
        "provider": provider,
        "error": error,
        "config": database_public_config(root) if persist else {
            "provider": provider,
            "database_url": "****" if "://" in url else url,
        },
    }
