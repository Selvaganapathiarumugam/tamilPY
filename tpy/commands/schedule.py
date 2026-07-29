"""
CLI commands for the task scheduler.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer

from tpy.utils.console import Console

schedule_app = typer.Typer(help="Run and inspect scheduled tasks.")


def register(app: typer.Typer) -> None:
    """Register ``tpy schedule`` subcommands."""
    app.add_typer(schedule_app, name="schedule")


@schedule_app.command("run")
def schedule_run(
    date: str | None = typer.Option(
        None,
        "--date",
        help="Simulate time as ISO datetime (testing)",
    ),
) -> None:
    """Run all due scheduled events once."""
    from tpy.schedule import Scheduler, load_schedule_module

    root = Path(".")
    scheduler = Scheduler(mutex_path=root / "storage" / "framework")
    load_schedule_module(root, scheduler)

    if not scheduler.events:
        Console.warning(
            "No scheduled events. Create app/schedule.py with register(scheduler)."
        )
        return

    moment = datetime.fromisoformat(date) if date else datetime.now()
    ran = scheduler.run(moment)
    if not ran:
        Console.info("No due events.")
        return
    for name in ran:
        Console.success(f"Ran: {name}")


@schedule_app.command("list")
def schedule_list() -> None:
    """List registered schedule events."""
    from tpy.schedule import Scheduler, load_schedule_module

    root = Path(".")
    scheduler = Scheduler(mutex_path=root / "storage" / "framework")
    load_schedule_module(root, scheduler)
    if not scheduler.events:
        Console.warning("No scheduled events registered.")
        return
    for event in scheduler.events:
        Console.info(
            f"{event.description} — cron `{event.expression.expression}`"
        )
