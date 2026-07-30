"""Auth sidecar for Studio (``.tpy/studio.json``) — not stored in schema.tpy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_AUTH: dict[str, Any] = {
    "enabled": False,
    "roles": ["super-admin", "admin", "developer"],
    "bootstrap_email": "admin@example.com",
    "bootstrap_password": None,
}


def studio_dir(project_root: Path) -> Path:
    return Path(project_root) / ".tpy"


def auth_path(project_root: Path) -> Path:
    return studio_dir(project_root) / "studio.json"


def load_auth(project_root: Path) -> dict[str, Any]:
    """Load auth config; passwords never returned in clear once set."""
    path = auth_path(project_root)
    data = dict(DEFAULT_AUTH)
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        data.update(raw)
    password = data.get("bootstrap_password")
    public = {
        "enabled": bool(data.get("enabled")),
        "roles": list(data.get("roles") or DEFAULT_AUTH["roles"]),
        "bootstrap_email": data.get("bootstrap_email"),
        "bootstrap_password_set": bool(password),
    }
    # Detect auth from project marker / models
    if (Path(project_root) / ".tpy_auth").exists():
        public["enabled"] = True
    return public


def save_auth(project_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Merge and persist auth sidecar.

    ``bootstrap_password`` is write-only; omit or null to keep existing.
    """
    path = auth_path(project_root)
    studio_dir(project_root).mkdir(parents=True, exist_ok=True)
    current: dict[str, Any] = dict(DEFAULT_AUTH)
    if path.exists():
        current.update(json.loads(path.read_text(encoding="utf-8")))

    if "enabled" in payload:
        current["enabled"] = bool(payload["enabled"])
    if "roles" in payload and payload["roles"] is not None:
        current["roles"] = [str(r) for r in payload["roles"]]
    if "bootstrap_email" in payload:
        current["bootstrap_email"] = payload["bootstrap_email"]
    if payload.get("bootstrap_password"):
        current["bootstrap_password"] = str(payload["bootstrap_password"])

    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return load_auth(project_root)
