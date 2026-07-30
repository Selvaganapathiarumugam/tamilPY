"""
Application scheduler registry.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from tpy.schedule.event import Callback, ScheduledEvent


class Scheduler:
    """
    Collect and run scheduled callbacks / jobs.

    Args:
        queue: Optional ``tpy.queue.Queue`` used by ``job()`` entries.
        mutex_path: Directory for ``without_overlapping`` lock files.
    """

    def __init__(
        self,
        queue: Any | None = None,
        mutex_path: Path | str = "storage/framework",
    ) -> None:
        self.queue = queue
        self.mutex_path = Path(mutex_path)
        self.events: list[ScheduledEvent] = []

    def call(
        self,
        callback: Callback,
        description: str | None = None,
    ) -> ScheduledEvent:
        """Schedule a synchronous callable."""
        event = ScheduledEvent(callback=callback, description=description)
        self.events.append(event)
        return event

    def job(self, job: Any, description: str | None = None) -> ScheduledEvent:
        """
        Schedule a ``Job`` instance.

        When due, the job is ``queue.push``'d if a queue is configured;
        otherwise ``job.handle()`` runs inline.
        """
        event = ScheduledEvent(job=job, description=description)
        self.events.append(event)
        return event

    def due_events(self, moment: datetime | None = None) -> list[ScheduledEvent]:
        """Return events due at ``moment``."""
        moment = moment or datetime.now()
        return [event for event in self.events if event.is_due(moment)]

    def run(self, moment: datetime | None = None) -> list[str]:
        """
        Execute all due events.

        Returns:
            Descriptions of events that ran.
        """
        moment = moment or datetime.now()
        ran: list[str] = []
        for event in self.due_events(moment):
            if not event.acquire_mutex(self.mutex_path):
                continue
            try:
                self._execute(event)
                ran.append(event.description)
            finally:
                event.release_mutex(self.mutex_path)
        return ran

    def _execute(self, event: ScheduledEvent) -> None:
        if event.job is not None:
            if self.queue is not None:
                self.queue.push(event.job)
            else:
                event.job.handle()
            return
        if event.callback is not None:
            event.callback()


def load_schedule_module(
    project_root: Path | str = ".",
    scheduler: Scheduler | None = None,
) -> Scheduler:
    """
    Load ``app/schedule.py`` and invoke ``register(scheduler)``.

    Args:
        project_root: Project root containing ``app/schedule.py``.
        scheduler: Existing scheduler to populate (created if omitted).

    Returns:
        Populated scheduler (unchanged if no schedule module exists).
    """
    import importlib.util

    root = Path(project_root)
    path = root / "app" / "schedule.py"
    scheduler = scheduler or Scheduler(mutex_path=root / "storage" / "framework")
    if not path.exists():
        return scheduler

    spec = importlib.util.spec_from_file_location("tpy_app_schedule", path)
    if spec is None or spec.loader is None:
        return scheduler
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    register: Callable | None = getattr(module, "register", None)
    if callable(register):
        register(scheduler)
    return scheduler
