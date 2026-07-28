"""
End-to-end CLI smoke: new → build → migrate → serve → /health.
"""

from __future__ import annotations

from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_cli_new_build_migrate_serve_health(tmp_path: Path):
    python = sys.executable
    project = tmp_path / "demoapp"

    subprocess.run(
        [python, "-m", "tpy.cli", "new", "demoapp"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert (project / "schema.tpy").exists()

    (project / "schema.tpy").write_text(
        """
database sqlite

model Item {
  id: uuid primary
  name: string required
}
""",
        encoding="utf-8",
    )
    (project / ".env").write_text(
        "TPY_DATABASE=sqlite\n"
        f"DATABASE_URL=sqlite:///{(project / 'database' / 'database.sqlite3').as_posix()}\n"
        "TPY_HOST=127.0.0.1\n"
        "TPY_PORT=8000\n",
        encoding="utf-8",
    )

    subprocess.run(
        [python, "-m", "tpy.cli", "build", "--skip-db"],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [python, "-m", "tpy.cli", "migrate"],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )

    port = _free_port()
    proc = subprocess.Popen(
        [
            python,
            "-m",
            "tpy.cli",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-reload",
        ],
        cwd=project,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        url = f"http://127.0.0.1:{port}/health"
        deadline = time.time() + 20
        last_error = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=1) as response:
                    body = response.read().decode("utf-8")
                    assert response.status == 200
                    assert "ok" in body
                    return
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                last_error = error
                time.sleep(0.25)
        raise AssertionError(f"/health not ready: {last_error}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
