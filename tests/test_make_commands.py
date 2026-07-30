"""Tests for ``tpy make:*`` and generated-file markers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tpy.exceptions import GeneratedFileConflict
from tpy.generator.make_generator import (
    MakeGenerator,
    parse_field_specs,
    split_field_specs,
)
from tpy.schema import parse_file
from tpy.utils.generated import (
    MARKER_PREFIX,
    is_pristine,
    write_generated,
)


def test_split_field_specs_respects_enum_parens() -> None:
    specs = split_field_specs(
        "amount:float,status:enum(draft,paid),user_id:uuid references User"
    )
    assert specs == [
        "amount:float",
        "status:enum(draft,paid)",
        "user_id:uuid references User",
    ]


def test_parse_field_specs() -> None:
    fields = parse_field_specs(
        "amount:float,status:enum(draft,paid),note:string nullable"
    )
    assert [f.name for f in fields] == ["amount", "status", "note"]
    assert fields[1].datatype == "enum"
    assert fields[1].enum_values == ["draft", "paid"]


def test_write_generated_protects_manual_edits(tmp_path: Path) -> None:
    path = tmp_path / "sample.py"
    write_generated(path, "print('a')\n", force=True)
    assert path.read_text(encoding="utf-8").startswith(MARKER_PREFIX)
    assert is_pristine(path)

    path.write_text(
        path.read_text(encoding="utf-8") + "# edited\n",
        encoding="utf-8",
    )
    assert not is_pristine(path)
    with pytest.raises(GeneratedFileConflict):
        write_generated(path, "print('b')\n", force=False)
    write_generated(path, "print('b')\n", force=True)
    assert "print('b')" in path.read_text(encoding="utf-8")


def _seed_project(tmp_path: Path) -> Path:
    root = tmp_path / "appproj"
    root.mkdir()
    (root / "schema.tpy").write_text(
        """\
database sqlite

model User {
  id: uuid primary
  email: string unique required
}
""",
        encoding="utf-8",
    )
    return root


def test_make_model_appends_schema_and_files(tmp_path: Path) -> None:
    root = _seed_project(tmp_path)
    MakeGenerator(root, force=True).make_model(
        "Invoice",
        fields="amount:float,status:enum(draft,paid),user_id:uuid references User",
    )
    program = parse_file(root / "schema.tpy")
    assert [m.name for m in program.models] == ["User", "Invoice"]
    invoice = program.models[1]
    assert invoice.fields[0].name == "id"
    assert invoice.fields[0].constraints == ["primary"]
    assert (root / "app" / "models" / "invoice.py").exists()
    assert (root / "app" / "services" / "invoice.py").exists()
    assert (root / "app" / "controllers" / "invoice.py").exists()
    assert (root / "app" / "routes" / "invoice.py").exists()
    assert list(
        (root / "database" / "migrations").glob("*_invoice_migration.py")
    )


def test_make_service_requires_force_after_edit(tmp_path: Path) -> None:
    root = _seed_project(tmp_path)
    maker = MakeGenerator(root, force=True)
    maker.make_model("Invoice", fields="amount:float")
    service = root / "app" / "services" / "invoice.py"
    text = service.read_text(encoding="utf-8")
    service.write_text(text + "\n# manual\n", encoding="utf-8")

    with pytest.raises(GeneratedFileConflict):
        MakeGenerator(root, force=False).make_service("Invoice")

    MakeGenerator(root, force=True).make_service("Invoice")
    assert "# manual" not in service.read_text(encoding="utf-8")


def test_make_model_cli(tmp_path: Path) -> None:
    root = _seed_project(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tpy.cli",
            "make:model",
            "Invoice",
            "--fields",
            "amount:float,status:enum(draft,paid)",
            "--force",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "Invoice" in (root / "schema.tpy").read_text(encoding="utf-8")
