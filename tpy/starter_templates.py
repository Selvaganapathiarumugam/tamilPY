"""
Starter template registry for ``tpy new --template`` and ``tpy templates``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Bundled Jinja / project folders that are not starter templates.
_RESERVED = frozenset({"project", "admin", "generators", "auth"})


@dataclass(slots=True)
class TemplateInfo:
    """Metadata for one starter template."""

    name: str
    description: str
    models: list[str]
    path: Path

    @property
    def schema_path(self) -> Path:
        return self.path / "schema.tpy"

    @property
    def theme_path(self) -> Path:
        return self.path / "admin-theme.json"

    @property
    def seeds_dir(self) -> Path:
        return self.path / "seeds"

    @property
    def readme_path(self) -> Path:
        return self.path / "README.md"


def templates_root() -> Path:
    """Return the filesystem path to ``tpy/templates``."""
    return Path(__file__).resolve().parent / "templates"


def list_templates() -> list[TemplateInfo]:
    """Discover starter templates (directories with ``schema.tpy``)."""
    root = templates_root()
    registry_path = root / "registry.json"
    catalog: dict[str, dict] = {}
    if registry_path.exists():
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
        for entry in raw.get("templates", []):
            catalog[str(entry["name"])] = entry

    found: list[TemplateInfo] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in _RESERVED:
            continue
        if not (child / "schema.tpy").exists():
            continue
        meta = catalog.get(child.name, {})
        schema_text = (child / "schema.tpy").read_text(encoding="utf-8")
        models = meta.get("models") or _models_from_schema(schema_text)
        found.append(
            TemplateInfo(
                name=child.name,
                description=str(
                    meta.get("description")
                    or f"{child.name} starter schema"
                ),
                models=[str(m) for m in models],
                path=child,
            )
        )
    return found


def get_template(name: str) -> TemplateInfo:
    """
    Look up a starter template by name.

    Raises:
        KeyError: When the template does not exist.
    """
    for info in list_templates():
        if info.name == name:
            return info
    known = ", ".join(t.name for t in list_templates()) or "(none)"
    raise KeyError(f"Unknown template '{name}'. Available: {known}")


def read_schema(name: str) -> str:
    """Return the ``schema.tpy`` source for ``name``."""
    return get_template(name).schema_path.read_text(encoding="utf-8")


def load_theme(
    name: str | None = None,
    project_root: Path | str | None = None,
) -> dict:
    """
    Load admin theme JSON.

    Preference: project ``admin-theme.json``, then template theme, then defaults.
    """
    defaults = {
        "title": "Admin",
        "accent": "#2563eb",
        "landing_model": None,
        "subtitle": "tamilPY dashboard",
    }
    if project_root is not None:
        local = Path(project_root) / "admin-theme.json"
        if local.exists():
            data = json.loads(local.read_text(encoding="utf-8"))
            return {**defaults, **data}
    if name:
        theme_path = get_template(name).theme_path
        if theme_path.exists():
            data = json.loads(theme_path.read_text(encoding="utf-8"))
            return {**defaults, **data}
    return defaults


def apply_template_files(project_root: Path, name: str) -> TemplateInfo:
    """
    Copy template schema, theme, seeds, and README notes into a project.
    """
    info = get_template(name)
    root = Path(project_root)
    (root / "schema.tpy").write_text(
        info.schema_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    if info.theme_path.exists():
        (root / "admin-theme.json").write_text(
            info.theme_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    seeds_dest = root / "database" / "seeds"
    seeds_dest.mkdir(parents=True, exist_ok=True)
    if info.seeds_dir.is_dir():
        for seed in info.seeds_dir.glob("*.py"):
            (seeds_dest / seed.name).write_text(
                seed.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
    if info.readme_path.exists():
        note = info.readme_path.read_text(encoding="utf-8")
        project_readme = root / "README.md"
        if project_readme.exists():
            project_readme.write_text(
                project_readme.read_text(encoding="utf-8")
                + "\n\n## Starter template\n\n"
                + note,
                encoding="utf-8",
            )
        else:
            project_readme.write_text(note, encoding="utf-8")
    return info


def _models_from_schema(source: str) -> list[str]:
    names: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("model "):
            parts = stripped.split()
            if len(parts) >= 2:
                names.append(parts[1].rstrip("{").strip())
    return names
