"""Tests for logging and configuration managers."""

from __future__ import annotations

from pathlib import Path

from tpy.config import Config, ConfigLoader
from tpy.kernel import Application
from tpy.logging import LogManager, get_logger, reset_log_manager


def test_log_manager_channels(tmp_path: Path, capsys):
    reset_log_manager()
    manager = LogManager()
    manager.configure(level="DEBUG", log_dir=tmp_path, app_name="demo")
    manager.channel("console").info("hello", user="a")
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "user='a'" in captured.out
    log_file = tmp_path / "demo.log"
    manager.channel("file").warning("file-line")
    assert log_file.exists()
    assert "file-line" in log_file.read_text(encoding="utf-8")
    reset_log_manager()


def test_get_logger_writes_file(tmp_path: Path):
    reset_log_manager()
    logger = get_logger("app", log_dir=tmp_path)
    logger.error("boom")
    assert (tmp_path / "app.log").exists()
    reset_log_manager()


def test_config_load_get_set(tmp_path: Path):
    (tmp_path / "tpy.toml").write_text(
        'name = "demo"\nversion = "1.2.3"\ndatabase = "sqlite"\n',
        encoding="utf-8",
    )
    cfg = Config.load(tmp_path)
    assert cfg.get("app.name") == "demo"
    assert cfg.get("app.version") == "1.2.3"
    assert cfg.has("database.driver")
    cfg.set("cache.driver", "file")
    assert cfg.get("cache.driver") == "file"
    assert cfg.section("app")["name"] == "demo"


def test_config_cache_roundtrip(tmp_path: Path):
    (tmp_path / "tpy.toml").write_text(
        'name = "cached"\ndatabase = "sqlite"\n',
        encoding="utf-8",
    )
    cfg = Config.load(tmp_path)
    path = cfg.cache()
    assert path.exists()
    loaded = Config.load_cached(tmp_path)
    assert loaded.get("app.name") == "cached"
    assert cfg.clear_cache() is True


def test_config_load_auto_freshness(tmp_path: Path, monkeypatch):
    import time

    (tmp_path / "tpy.toml").write_text(
        'name = "auto"\ndatabase = "sqlite"\n',
        encoding="utf-8",
    )
    cfg = Config.load(tmp_path)
    cfg.cache()
    assert cfg.cache_is_fresh() is True

    monkeypatch.delenv("TPY_CONFIG_CACHE", raising=False)
    live = Config.load_auto(tmp_path)
    assert live.get("app.name") == "auto"

    monkeypatch.setenv("TPY_CONFIG_CACHE", "1")
    cached = Config.load_auto(tmp_path)
    assert cached.get("app.name") == "auto"

    time.sleep(0.05)
    (tmp_path / "tpy.toml").write_text(
        'name = "stale"\ndatabase = "sqlite"\n',
        encoding="utf-8",
    )
    probe = Config(base_path=tmp_path)
    assert probe.cache_is_fresh() is False
    refreshed = Config.load_auto(tmp_path, prefer_cache=True)
    # Stale cache → falls back to load()
    assert refreshed.get("app.name") == "stale"


def test_config_loader_soft_break(tmp_path: Path):
    (tmp_path / "tpy.toml").write_text(
        'name = "legacy"\ndatabase = "sqlite"\n',
        encoding="utf-8",
    )
    settings = ConfigLoader(tmp_path).load()
    assert settings.name == "legacy"


def test_application_binds_config_and_log(tmp_path: Path):
    (tmp_path / "tpy.toml").write_text(
        'name = "kernel-app"\ndatabase = "sqlite"\n',
        encoding="utf-8",
    )
    (tmp_path / "storage" / "logs").mkdir(parents=True)
    app = Application(tmp_path).with_framework_providers().boot()
    assert app.config.get("app.name") == "kernel-app"
    app.log.channel().info("from-kernel")
    assert (tmp_path / "storage" / "logs" / "kernel-app.log").exists()
