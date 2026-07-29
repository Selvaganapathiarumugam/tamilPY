"""
Redis list-backed queue driver (optional dependency).
"""

from __future__ import annotations

from typing import Any

from tpy.queue.drivers.base import QueueDriver, ReservedJob
from tpy.queue.exceptions import DriverError
from tpy.queue.job import Job
from tpy.queue.serializer import deserialize_job, serialize_job


class RedisQueueDriver(QueueDriver):
    """
    Simple Redis list queue.

    Requires the ``redis`` package (``pip install tamilPY[redis]``).
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        client: Any | None = None,
        key_prefix: str = "tpy:queue:",
    ) -> None:
        self.key_prefix = key_prefix
        if client is not None:
            self.client = client
            return
        try:
            import redis
        except ImportError as error:
            raise DriverError(
                "Redis driver requires the 'redis' package. "
                "Install with: pip install tamilPY[redis]"
            ) from error
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)

    def _key(self, queue: str) -> str:
        return f"{self.key_prefix}{queue}"

    def push(self, job: Job, queue: str | None = None) -> None:
        name = queue or job.queue
        self.client.rpush(self._key(name), serialize_job(job, attempts=0))

    def pop(self, queue: str = "default") -> ReservedJob | None:
        raw = self.client.lpop(self._key(queue))
        if raw is None:
            return None
        job, meta = deserialize_job(raw)
        attempts = int(meta["attempts"]) + 1
        return ReservedJob(
            job=job,
            attempts=attempts,
            tries=int(meta["tries"]),
            queue=queue,
            receipt={"raw": serialize_job(job, attempts=attempts)},
        )

    def ack(self, reserved: ReservedJob) -> None:
        return None

    def release(self, reserved: ReservedJob, delay: float = 0) -> None:
        self.client.rpush(
            self._key(reserved.queue),
            serialize_job(reserved.job, attempts=reserved.attempts),
        )

    def fail(self, reserved: ReservedJob, error: BaseException) -> None:
        reserved.job.failed(error)
        self.client.rpush(
            f"{self.key_prefix}failed:{reserved.queue}",
            json_dumps_safe(reserved, error),
        )


def json_dumps_safe(reserved: ReservedJob, error: BaseException) -> str:
    import json

    return json.dumps(
        {
            "payload": serialize_job(reserved.job, attempts=reserved.attempts),
            "exception": repr(error),
        }
    )
