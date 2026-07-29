"""Tests for CLI UX and watch mode helpers."""

from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from tpy.cli import app
from tpy.commands import watch as watch_mod


runner = CliRunner()


def test_cli_version_flag():
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert "tamilPY" in result.stdout


def test_cli_about():
    result = runner.invoke(app, ["about"])
    assert result.exit_code == 0
    assert "Package" in result.stdout or "tamilPY" in result.stdout


def test_cli_commands_lists_watch():
    result = runner.invoke(app, ["commands"])
    assert result.exit_code == 0
    assert "watch" in result.stdout
    assert "optimize" in result.stdout


def test_watch_fingerprint(tmp_path: Path):
    schema = tmp_path / "schema.tpy"
    schema.write_text("database sqlite\n", encoding="utf-8")
    stamps = watch_mod._fingerprint([schema, tmp_path / "tpy.toml"])
    assert stamps[0] > 0
    assert stamps[1] == 0.0


def test_config_status_command(tmp_path: Path, monkeypatch):
    (tmp_path / "tpy.toml").write_text(
        'name = "cli"\ndatabase = "sqlite"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["config", "status"])
    assert result.exit_code == 0
    assert "Fresh" in result.stdout or "fresh" in result.stdout.lower()
