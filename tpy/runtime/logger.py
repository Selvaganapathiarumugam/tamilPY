from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from pathlib import Path
import sys


class LogLevel(IntEnum):
    """Supported log severity levels."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


class Logger:
    """
    Simple file + console logger for TPY client applications.

    Prefer ``tpy.logging.get_logger`` / ``LogManager`` for new code
    (stdlib channels + context).
    """

    def __init__(
        self,
        name: str = "tpy",
        level: LogLevel = LogLevel.INFO,
        log_file: Path | str | None = None,
    ) -> None:
        self.name = name
        self.level = level
        self.log_file = Path(log_file) if log_file else None

        if self.log_file is not None:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self._write(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        """Log an info message."""
        self._write(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self._write(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        """Log an error message."""
        self._write(LogLevel.ERROR, message)

    def _write(self, level: LogLevel, message: str) -> None:
        if level < self.level:
            return

        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] {level.name} {self.name}: {message}"

        stream = sys.stderr if level >= LogLevel.ERROR else sys.stdout
        print(line, file=stream)

        if self.log_file is not None:
            with self.log_file.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")


def get_logger(
    name: str = "app",
    log_dir: Path | str = "storage/logs",
) -> Logger:
    """
    Create a project logger that writes to ``storage/logs/app.log``.

    Args:
        name: Logger name.
        log_dir: Directory for log files.

    Returns:
        Configured ``Logger`` instance.
    """
    return Logger(
        name=name,
        log_file=Path(log_dir) / f"{name}.log",
    )
