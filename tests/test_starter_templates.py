"""Tests for starter templates and ``tpy new --template``."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tpy.schema import parse_source, validate_program
from tpy.starter_templates import (
    apply_template_files,
    list_templates,
    load_theme,
    read_schema,
)


def test_registry_lists_five_templates() -> None:
    names = {info.name for info in list_templates()}
    assert names == {
        "crm",
        "institute-admin",
        "inventory",
        "helpdesk",
        "blog-cms",
    }


def test_each_template_schema_validates() -> None:
    for info in list_templates():
        program = parse_source(read_schema(info.name))
        diagnostics = validate_program(program, filename=f"{info.name}.tpy")
        errors = [d for d in diagnostics if d.severity == "error"]
        assert not errors, f"{info.name}: {errors}"


def test_new_with_template_cli(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tpy.cli",
            "new",
            "crmapp",
            "--template",
            "crm",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    project = tmp_path / "crmapp"
    schema = (project / "schema.tpy").read_text(encoding="utf-8")
    assert "model Company" in schema
    assert (project / "admin-theme.json").exists()
    theme = json.loads((project / "admin-theme.json").read_text(encoding="utf-8"))
    assert theme["landing_model"] == "Company"
    assert (project / "database" / "seeds" / "crm_seed.py").exists()


def test_templates_list_and_show_cli() -> None:
    listed = subprocess.run(
        [sys.executable, "-m", "tpy.cli", "templates", "list"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert listed.returncode == 0
    assert "crm" in listed.stdout + listed.stderr

    shown = subprocess.run(
        [sys.executable, "-m", "tpy.cli", "templates", "show", "crm"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert shown.returncode == 0
    assert "model Company" in shown.stdout


def test_apply_template_and_theme_load(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    (root / "README.md").write_text("# App\n", encoding="utf-8")
    apply_template_files(root, "helpdesk")
    theme = load_theme(project_root=root)
    assert theme["title"] == "Helpdesk"
    assert theme["accent"].startswith("#")
