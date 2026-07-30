"""
Framework logging — channels, levels, and structured context.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from tpy.runtime.logger import LogLevel


class ContextLogger:
    """
    Thin wrapper around ``logging.Logger`` with optional context fields.
    """

    def __init__(
        self,
        logger: logging.Logger,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._logger = logger
        self._context = dict(context or {})

    def with_context(self, **kwargs: Any) -> ContextLogger:
        """Return a child logger with merged context."""
        merged = {**self._context, **kwargs}
        return ContextLogger(self._logger, merged)

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, kwargs, exc_info=True)

    def _log(
        self,
        level: int,
        message: str,
        extra_fields: dict[str, Any],
        exc_info: bool = False,
    ) -> None:
        payload = {**self._context, **extra_fields}
        if payload:
            suffix = " ".join(f"{key}={value!r}" for key, value in payload.items())
            message = f"{message} | {suffix}"
        self._logger.log(level, message, exc_info=exc_info)


class LogManager:
    """
    Configure and resolve named logging channels.

    Channels:
    - ``console`` — stderr/stdout via StreamHandler
    - ``file`` — rotating-style append file under ``storage/logs``
    - ``stack`` — both (default)
    """

    def __init__(self) -> None:
        self._channels: dict[str, ContextLogger] = {}
        self._default = "stack"
        self._configured = False

    def configure(
        self,
        *,
        level: str | int | LogLevel = "INFO",
        log_dir: Path | str = "storage/logs",
        app_name: str = "app",
        default: str = "stack",
    ) -> LogManager:
        """
        Configure console + file channels.

        Idempotent for the same process; reconfigure replaces handlers.
        """
        numeric = self._coerce_level(level)
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_path = log_path / f"{app_name}.log"

        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_logger = logging.getLogger(f"tpy.{app_name}.console")
        file_logger = logging.getLogger(f"tpy.{app_name}.file")
        stack_logger = logging.getLogger(f"tpy.{app_name}")

        for logger in (console_logger, file_logger, stack_logger):
            logger.handlers.clear()
            logger.setLevel(numeric)
            logger.propagate = False

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric)
        console_logger.addHandler(console_handler)

        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric)
        file_logger.addHandler(file_handler)

        stack_logger.addHandler(console_handler)
        stack_logger.addHandler(file_handler)

        self._channels = {
            "console": ContextLogger(console_logger),
            "file": ContextLogger(file_logger),
            "stack": ContextLogger(stack_logger),
        }
        self._default = default if default in self._channels else "stack"
        self._configured = True
        return self

    def channel(self, name: str | None = None) -> ContextLogger:
        """Return a named channel (configures defaults when needed)."""
        if not self._configured:
            self.configure()
        key = name or self._default
        if key not in self._channels:
            raise KeyError(f"Unknown log channel: {key}")
        return self._channels[key]

    def get(self, name: str = "app") -> ContextLogger:
        """Alias used by applications — default stack channel with name context."""
        return self.channel().with_context(logger=name)

    @staticmethod
    def _coerce_level(level: str | int | LogLevel) -> int:
        if isinstance(level, LogLevel):
            return int(level)
        if isinstance(level, int):
            return level
        return getattr(logging, str(level).upper(), logging.INFO)


_manager: LogManager | None = None


def log_manager() -> LogManager:
    """Process-wide ``LogManager`` singleton."""
    global _manager
    if _manager is None:
        _manager = LogManager()
    return _manager


def get_logger(
    name: str = "app",
    log_dir: Path | str = "storage/logs",
) -> ContextLogger:
    """
    Framework logger entry point (stdio logging).

    Soft-compatible replacement for ``tpy.runtime.logger.get_logger`` when
    callers only need ``debug/info/warning/error``.
    """
    manager = log_manager()
    if not manager._configured:
        manager.configure(log_dir=log_dir, app_name=name)
    return manager.channel("stack").with_context(logger=name)


def reset_log_manager() -> None:
    """Reset the singleton (tests)."""
    global _manager
    _manager = None
