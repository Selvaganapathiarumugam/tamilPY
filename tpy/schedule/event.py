"""
A single scheduled callback or job.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from tpy.schedule.cron import CronExpression
from tpy.schedule.exceptions import ScheduleError

Callback = Callable[[], Any]


class ScheduledEvent:
    """
    Fluent schedule entry bound to a callback or queue job.
    """

    def __init__(
        self,
        callback: Callback | None = None,
        job: Any | None = None,
        description: str | None = None,
    ) -> None:
        if callback is None and job is None:
            raise ScheduleError("ScheduledEvent requires callback or job")
        self.callback = callback
        self.job = job
        self.description = description or self._default_description()
        self.expression = CronExpression("* * * * *")
        self._without_overlapping = False
        self._mutex_expires = 60 * 60
        self._filters: list[Callable[[], bool]] = []

    def _default_description(self) -> str:
        if self.job is not None:
            return type(self.job).__name__
        if self.callback is not None:
            return getattr(self.callback, "__name__", repr(self.callback))
        return "event"

    def cron(self, expression: str) -> ScheduledEvent:
        """Set a raw 5-field cron expression."""
        self.expression = CronExpression(expression)
        return self

    def every_minute(self) -> ScheduledEvent:
        """Run every minute."""
        return self.cron("* * * * *")

    def every_five_minutes(self) -> ScheduledEvent:
        """Run every five minutes."""
        return self.cron("*/5 * * * *")

    def every_ten_minutes(self) -> ScheduledEvent:
        """Run every ten minutes."""
        return self.cron("*/10 * * * *")

    def every_thirty_minutes(self) -> ScheduledEvent:
        """Run every thirty minutes."""
        return self.cron("*/30 * * * *")

    def hourly(self) -> ScheduledEvent:
        """Run at the start of every hour."""
        return self.cron("0 * * * *")

    def daily(self) -> ScheduledEvent:
        """Run daily at midnight."""
        return self.cron("0 0 * * *")

    def daily_at(self, time: str) -> ScheduledEvent:
        """
        Run daily at ``HH:MM`` (24h).

        Example: ``daily_at(\"08:30\")``.
        """
        hour_s, minute_s = time.split(":", 1)
        return self.cron(f"{int(minute_s)} {int(hour_s)} * * *")

    def weekly(self) -> ScheduledEvent:
        """Run weekly on Sunday at midnight."""
        return self.cron("0 0 * * 0")

    def weekdays(self) -> ScheduledEvent:
        """Run Monday–Friday at midnight."""
        return self.cron("0 0 * * 1-5")

    def when(self, predicate: Callable[[], bool]) -> ScheduledEvent:
        """Only run when ``predicate()`` is true."""
        self._filters.append(predicate)
        return self

    def without_overlapping(self, expires_at: int = 3600) -> ScheduledEvent:
        """Skip run if a previous invocation still holds the mutex."""
        self._without_overlapping = True
        self._mutex_expires = expires_at
        return self

    def name(self, description: str) -> ScheduledEvent:
        """Set a human-readable description."""
        self.description = description
        return self

    def is_due(self, moment: datetime | None = None) -> bool:
        """Return whether this event should run at ``moment``."""
        moment = moment or datetime.now()
        if not self.expression.is_due(moment):
            return False
        return all(pred() for pred in self._filters)

    def mutex_path(self, base: Path) -> Path:
        """Return lock file path for overlap protection."""
        digest = hashlib.sha256(self.description.encode("utf-8")).hexdigest()[:16]
        return base / f"schedule-{digest}.lock"

    def acquire_mutex(self, base: Path) -> bool:
        """Try to acquire the overlap mutex. Return False if locked."""
        if not self._without_overlapping:
            return True
        path = self.mutex_path(base)
        path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now().timestamp()
        if path.exists():
            try:
                created = float(path.read_text(encoding="utf-8").strip() or "0")
            except ValueError:
                created = 0
            if now - created < self._mutex_expires:
                return False
        path.write_text(str(now), encoding="utf-8")
        return True

    def release_mutex(self, base: Path) -> None:
        """Release the overlap mutex when present."""
        if not self._without_overlapping:
            return
        path = self.mutex_path(base)
        if path.exists():
            path.unlink()
