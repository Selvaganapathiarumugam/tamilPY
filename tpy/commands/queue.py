"""
CLI commands for background queues.
"""

from __future__ import annotations

from pathlib import Path

import typer

from tpy.utils.console import Console

queue_app = typer.Typer(help="Manage background job queues.")


def register(app: typer.Typer) -> None:
    """Register ``tpy queue`` subcommands."""
    app.add_typer(queue_app, name="queue")


@queue_app.command("table")
def queue_table() -> None:
    """Create ``_tpy_jobs`` / ``_tpy_failed_jobs`` tables."""
    from tpy.providers.factory import get_provider
    from tpy.queue import DatabaseQueueDriver

    root = Path(".")
    provider = get_provider(project_root=root)
    try:
        provider.connect()
        driver = DatabaseQueueDriver(provider)
        driver.ensure_tables()
        Console.success("Queue tables ready (_tpy_jobs, _tpy_failed_jobs).")
    finally:
        provider.close()


@queue_app.command("work")
def queue_work(
    driver: str = typer.Option(
        "database",
        "--driver",
        "-d",
        help="Queue driver: database | sync | redis",
    ),
    name: str = typer.Option("default", "--queue", "-q", help="Queue name"),
    once: bool = typer.Option(False, "--once", help="Process one job and exit"),
    sleep: float = typer.Option(1.0, "--sleep", help="Sleep when empty"),
    redis_url: str = typer.Option(
        "redis://localhost:6379/0",
        "--redis-url",
        help="Redis URL when --driver=redis",
    ),
) -> None:
    """Run a queue worker."""
    from tpy.queue import Queue, Worker

    queue_driver = _build_driver(driver, redis_url=redis_url)
    worker = Worker(Queue(queue_driver), sleep=sleep, once=once)
    Console.info(f"Queue worker started (driver={driver}, queue={name})")
    processed = worker.run(name=name)
    Console.success(f"Processed {processed} job(s).")


def _build_driver(driver: str, redis_url: str):
    driver = driver.lower()
    if driver == "sync":
        from tpy.queue import SyncQueueDriver

        return SyncQueueDriver()
    if driver == "redis":
        from tpy.queue.drivers.redis import RedisQueueDriver

        return RedisQueueDriver(redis_url=redis_url)
    if driver == "database":
        from tpy.providers.factory import get_provider
        from tpy.queue import DatabaseQueueDriver

        provider = get_provider(project_root=Path("."))
        provider.connect()
        db_driver = DatabaseQueueDriver(provider)
        db_driver.ensure_tables()
        return db_driver
    Console.error(f"Unknown queue driver: {driver}")
    raise typer.Exit(1)
