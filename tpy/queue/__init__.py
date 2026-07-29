"""
tamilPY Queue & Background Jobs.
"""

from tpy.queue.drivers import (
    DatabaseQueueDriver,
    QueueDriver,
    ReservedJob,
    SyncQueueDriver,
)
from tpy.queue.exceptions import DriverError, JobError, QueueError
from tpy.queue.job import Job
from tpy.queue.queue import Queue
from tpy.queue.worker import Worker

__all__ = [
    "DatabaseQueueDriver",
    "DriverError",
    "Job",
    "JobError",
    "Queue",
    "QueueDriver",
    "QueueError",
    "ReservedJob",
    "SyncQueueDriver",
    "Worker",
]


def __getattr__(name: str):
    if name == "RedisQueueDriver":
        from tpy.queue.drivers.redis import RedisQueueDriver

        return RedisQueueDriver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
