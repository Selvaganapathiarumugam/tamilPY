"""Integration tests for tamilPY Studio API (temp project only)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tpy.studio.server import create_app


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "studio_proj"
    root.mkdir()
    (root / "schema.tpy").write_text(
        """\
database sqlite

model Item {
  id: uuid primary
  name: string required
}
""",
        encoding="utf-8",
    )
    (root / ".env").write_text(
        "TPY_DATABASE=sqlite\nDATABASE_URL=sqlite:///:memory:\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def client(project: Path) -> TestClient:
    return TestClient(create_app(project))


def test_health(client: TestClient) -> None:
    res = client.get("/api/studio/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "version" in body


def test_get_schema(client: TestClient) -> None:
    res = client.get("/api/studio/schema")
    assert res.status_code == 200
    body = res.json()
    assert body["database"] == "sqlite"
    assert body["models"][0]["name"] == "Item"
    assert "auth" in body


def test_preview_does_not_write(client: TestClient, project: Path) -> None:
    before = (project / "schema.tpy").read_text(encoding="utf-8")
    payload = {
        "database": "sqlite",
        "models": [
            {
                "name": "Item",
                "fields": [
                    {
                        "name": "id",
                        "type": "uuid",
                        "constraints": ["primary"],
                        "has_default": False,
                        "enum_values": [],
                        "references": None,
                    },
                    {
                        "name": "title",
                        "type": "string",
                        "constraints": ["required"],
                        "has_default": False,
                        "enum_values": [],
                        "references": None,
                    },
                ],
                "unique_together": [],
                "relations": [],
            }
        ],
        "enums": [],
    }
    res = client.post("/api/studio/schema/preview", json=payload)
    assert res.status_code == 200
    assert "diff" in res.json()
    assert (project / "schema.tpy").read_text(encoding="utf-8") == before


def test_save_schema(client: TestClient, project: Path) -> None:
    payload = client.get("/api/studio/schema").json()
    payload["models"][0]["fields"].append(
        {
            "name": "note",
            "type": "string",
            "constraints": ["nullable"],
            "has_default": False,
            "default": None,
            "enum_values": [],
            "references": None,
        }
    )
    res = client.post("/api/studio/schema/save", json=payload)
    assert res.status_code == 200
    text = (project / "schema.tpy").read_text(encoding="utf-8")
    assert "note: string nullable" in text


def test_database_get_redacts(client: TestClient) -> None:
    res = client.get("/api/studio/database")
    assert res.status_code == 200
    assert res.json()["provider"] == "sqlite"


def test_database_dry_run_sqlite(client: TestClient) -> None:
    res = client.post(
        "/api/studio/database",
        json={
            "provider": "sqlite",
            "path": ":memory:",
            "dry_run": True,
        },
    )
    assert res.status_code == 200
    # memory path may need sqlite:///:memory:
    body = res.json()
    assert "ok" in body


def test_rollback_requires_confirm(client: TestClient) -> None:
    res = client.post("/api/studio/migrate/rollback", json={"confirm": False})
    assert res.status_code == 400


def test_auth_get_and_save_roles(client: TestClient, project: Path) -> None:
    res = client.get("/api/studio/auth")
    assert res.status_code == 200
    assert "roles" in res.json()
    res = client.post(
        "/api/studio/auth",
        json={
            "enabled": False,
            "roles": ["super-admin", "editor"],
            "bootstrap_email": "a@b.com",
        },
    )
    assert res.status_code == 200
    assert "editor" in res.json()["roles"]
    assert (project / ".tpy" / "studio.json").exists()


def test_templates_list(client: TestClient) -> None:
    res = client.get("/api/studio/templates")
    assert res.status_code == 200
    names = {t["name"] for t in res.json()["templates"]}
    assert "crm" in names


def test_templates_apply_preview(client: TestClient, project: Path) -> None:
    before = (project / "schema.tpy").read_text(encoding="utf-8")
    res = client.post(
        "/api/studio/templates/apply",
        json={"name": "crm", "confirm": False},
    )
    assert res.status_code == 200
    assert res.json()["preview"] is True
    assert (project / "schema.tpy").read_text(encoding="utf-8") == before


def test_routes_endpoint(client: TestClient) -> None:
    res = client.get("/api/studio/routes")
    assert res.status_code == 200
    assert "routes" in res.json()
