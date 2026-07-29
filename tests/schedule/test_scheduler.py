"""Tests for cron matcher and scheduler."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from tpy.queue import Job, Queue, SyncQueueDriver
from tpy.schedule import CronExpression, ScheduleError, Scheduler, load_schedule_module


def test_cron_every_five_minutes():
    cron = CronExpression("*/5 * * * *")
    assert cron.is_due(datetime(2026, 7, 28, 10, 0))
    assert cron.is_due(datetime(2026, 7, 28, 10, 5))
    assert not cron.is_due(datetime(2026, 7, 28, 10, 6))


def test_cron_daily_at():
    cron = CronExpression("30 8 * * *")
    assert cron.is_due(datetime(2026, 7, 28, 8, 30))
    assert not cron.is_due(datetime(2026, 7, 28, 8, 31))


def test_cron_rejects_bad_expression():
    with pytest.raises(ScheduleError):
        CronExpression("* * *")


def test_scheduler_runs_due_callback(tmp_path: Path):
    sink: list[str] = []
    scheduler = Scheduler(mutex_path=tmp_path / "locks")
    scheduler.call(lambda: sink.append("ok")).cron("30 8 * * *")
    assert scheduler.run(datetime(2026, 7, 28, 8, 29)) == []
    assert scheduler.run(datetime(2026, 7, 28, 8, 30)) == [
        scheduler.events[0].description
    ]
    assert sink == ["ok"]


def test_scheduler_job_uses_queue(tmp_path: Path):
    class Dig(Job):
        handled: list[str] = []

        def __init__(self, name: str = "n") -> None:
            self.name = name

        def handle(self) -> None:
            type(self).handled.append(self.name)

    Dig.handled = []
    queue = Queue(SyncQueueDriver())
    scheduler = Scheduler(queue=queue, mutex_path=tmp_path / "locks")
    scheduler.job(Dig("x")).every_minute()
    scheduler.run(datetime(2026, 7, 28, 12, 0))
    assert Dig.handled == ["x"]


def test_without_overlapping(tmp_path: Path):
    sink: list[int] = []
    scheduler = Scheduler(mutex_path=tmp_path)
    event = (
        scheduler.call(lambda: sink.append(1))
        .every_minute()
        .without_overlapping(expires_at=3600)
        .name("locked")
    )
    # Simulate held lock
    lock = event.mutex_path(tmp_path)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(str(datetime.now().timestamp()), encoding="utf-8")
    assert scheduler.run(datetime(2026, 7, 28, 1, 0)) == []
    assert sink == []


def test_load_schedule_module(tmp_path: Path):
    app = tmp_path / "app"
    app.mkdir()
    (app / "schedule.py").write_text(
        """
def register(scheduler):
    scheduler.call(lambda: None).hourly().name("heartbeat")
""",
        encoding="utf-8",
    )
    scheduler = load_schedule_module(tmp_path)
    assert len(scheduler.events) == 1
    assert scheduler.events[0].description == "heartbeat"


def test_daily_at_helper(tmp_path: Path):
    scheduler = Scheduler(mutex_path=tmp_path)
    scheduler.call(lambda: None).daily_at("09:15").name("morning")
    assert scheduler.events[0].expression.expression == "15 9 * * *"
