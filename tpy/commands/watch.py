"""
Watch mode — rebuild when schema.tpy (and related files) change.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import typer

from tpy.utils.console import Console


def register(app: typer.Typer) -> None:
    """Register the watch command."""

    @app.command("watch")
    def watch(
        interval: float = typer.Option(
            1.0,
            "--interval",
            "-i",
            help="Polling interval in seconds",
        ),
        skip_db: bool = typer.Option(
            True,
            "--skip-db/--with-db",
            help="Use tpy build --skip-db (default) or full build",
        ),
        once: bool = typer.Option(
            False,
            "--once",
            help="Run one rebuild if dirty then exit (for tests)",
        ),
    ) -> None:
        """
        Watch ``schema.tpy`` and rebuild CRUD when it changes.

        Uses stdlib polling (no extra dependencies). Pair with
        ``tpy serve --reload`` in another terminal for API reload.
        """
        root = Path(".").resolve()
        schema = root / "schema.tpy"
        if not schema.exists():
            Console.error("schema.tpy not found. Run inside a TPY project.")
            raise typer.Exit(1)

        watched = [schema, root / "tpy.toml"]
        Console.banner(_version())
        Console.info(
            f"Watching {[str(path.name) for path in watched if path.exists()]} "
            f"every {interval}s (Ctrl+C to stop)"
        )

        last_mtime = _fingerprint(watched)
        # Initial build when starting watch
        _rebuild(root, skip_db=skip_db)
        last_mtime = _fingerprint(watched)

        if once:
            return

        try:
            while True:
                time.sleep(interval)
                current = _fingerprint(watched)
                if current != last_mtime:
                    Console.warning("Change detected — rebuilding…")
                    _rebuild(root, skip_db=skip_db)
                    last_mtime = _fingerprint(watched)
                    Console.success("Rebuild complete.")
        except KeyboardInterrupt:
            Console.info("Watch stopped.")


def _fingerprint(paths: list[Path]) -> tuple[float, ...]:
    stamps: list[float] = []
    for path in paths:
        if path.exists():
            stamps.append(path.stat().st_mtime)
        else:
            stamps.append(0.0)
    return tuple(stamps)


def _rebuild(root: Path, *, skip_db: bool) -> None:
    args = [sys.executable, "-m", "tpy.cli", "build"]
    if skip_db:
        args.append("--skip-db")
    result = subprocess.run(args, cwd=root)
    if result.returncode != 0:
        Console.error("Rebuild failed — fix errors and save again.")


def _version() -> str:
    try:
        from importlib.metadata import version as pkg_version

        return pkg_version("tamilPY")
    except Exception:
        from tpy import __version__

        return __version__
