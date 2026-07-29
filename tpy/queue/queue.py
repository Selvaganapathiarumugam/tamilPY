"""
High-level queue facade.
"""

from __future__ import annotations

from tpy.queue.drivers.base import QueueDriver
from tpy.queue.job import Job


class Queue:
    """
    Application-facing queue API.

    Args:
        driver: Backend used to store and run jobs.
    """

    def __init__(self, driver: QueueDriver) -> None:
        self.driver = driver

    def push(self, job: Job, queue: str | None = None) -> None:
        """Push ``job`` onto the given queue name."""
        self.driver.push(job, queue=queue)

    def later(self, job: Job, delay: float = 0, queue: str | None = None) -> None:
        """
        Push a delayed job.

        Database/Redis delay support is best-effort in v0.1.9; ``sync`` runs
        immediately. ``delay`` is reserved for future drivers.
        """
        _ = delay
        self.push(job, queue=queue)

    def pop(self, queue: str = "default"):
        """Reserve the next job from ``queue``."""
        return self.driver.pop(queue)
