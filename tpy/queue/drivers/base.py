"""
Queue driver contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from tpy.queue.job import Job


@dataclass(slots=True)
class ReservedJob:
    """A job reserved from a driver for processing."""

    job: Job
    attempts: int
    tries: int
    queue: str
    receipt: Any = None


class QueueDriver(ABC):
    """Backend that stores and releases jobs."""

    @abstractmethod
    def push(self, job: Job, queue: str | None = None) -> None:
        """Enqueue ``job`` onto ``queue`` (or ``job.queue``)."""

    @abstractmethod
    def pop(self, queue: str = "default") -> ReservedJob | None:
        """Reserve the next available job, or ``None`` if empty."""

    @abstractmethod
    def ack(self, reserved: ReservedJob) -> None:
        """Mark ``reserved`` as successfully processed."""

    @abstractmethod
    def release(self, reserved: ReservedJob, delay: float = 0) -> None:
        """Return ``reserved`` to the queue for another attempt."""

    @abstractmethod
    def fail(self, reserved: ReservedJob, error: BaseException) -> None:
        """Record permanent failure for ``reserved``."""
