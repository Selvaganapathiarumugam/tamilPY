"""
Synchronous queue driver — runs jobs immediately on push.
"""

from __future__ import annotations

from tpy.queue.drivers.base import QueueDriver, ReservedJob
from tpy.queue.job import Job


class SyncQueueDriver(QueueDriver):
    """
    Execute jobs inline when pushed.

    Ideal for tests and local development. ``pop`` always returns ``None``.
    """

    def push(self, job: Job, queue: str | None = None) -> None:
        job.handle()

    def pop(self, queue: str = "default") -> ReservedJob | None:
        return None

    def ack(self, reserved: ReservedJob) -> None:
        return None

    def release(self, reserved: ReservedJob, delay: float = 0) -> None:
        return None

    def fail(self, reserved: ReservedJob, error: BaseException) -> None:
        job = reserved.job
        job.failed(error)
