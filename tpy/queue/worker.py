"""
Queue worker loop.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from tpy.queue.drivers.base import QueueDriver, ReservedJob
from tpy.queue.queue import Queue


class Worker:
    """
    Process reserved jobs from a queue driver.

    Args:
        queue: Queue facade (or pass ``driver`` via ``Queue(driver)``).
        sleep: Seconds to sleep when the queue is empty.
        once: Process at most one job then exit.
    """

    def __init__(
        self,
        queue: Queue,
        sleep: float = 1.0,
        once: bool = False,
        on_error: Callable[[ReservedJob, BaseException], None] | None = None,
    ) -> None:
        self.queue = queue
        self.sleep = sleep
        self.once = once
        self.on_error = on_error

    @property
    def driver(self) -> QueueDriver:
        return self.queue.driver

    def run(self, name: str = "default") -> int:
        """
        Run the worker loop.

        Returns:
            Number of jobs processed (success or fail).
        """
        processed = 0
        while True:
            reserved = self.queue.pop(name)
            if reserved is None:
                if self.once:
                    return processed
                time.sleep(self.sleep)
                continue

            self._run_job(reserved)
            processed += 1
            if self.once:
                return processed

    def _run_job(self, reserved: ReservedJob) -> None:
        try:
            reserved.job.handle()
        except BaseException as error:
            if self.on_error is not None:
                self.on_error(reserved, error)
            if reserved.attempts < reserved.tries:
                self.driver.release(reserved)
            else:
                self.driver.fail(reserved, error)
            return
        self.driver.ack(reserved)
