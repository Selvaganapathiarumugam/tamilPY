"""
Database-backed queue driver using a provider connection.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from tpy.queue.drivers.base import QueueDriver, ReservedJob
from tpy.queue.exceptions import DriverError
from tpy.queue.job import Job
from tpy.queue.serializer import deserialize_job, serialize_job


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DatabaseQueueDriver(QueueDriver):
    """
    Persist jobs in ``_tpy_jobs`` / ``_tpy_failed_jobs`` tables.

    Expects a provider with ``execute`` / ``fetch_one`` / ``fetch_all`` and
    ``PLACEHOLDER``.
    """

    JOBS_TABLE = "_tpy_jobs"
    FAILED_TABLE = "_tpy_failed_jobs"

    def __init__(self, connection: Any) -> None:
        self.connection = connection
        self._ph = getattr(connection, "PLACEHOLDER", "?")

    def ensure_tables(self) -> None:
        """Create queue tables when missing."""
        id_col = self._id_column_sql()
        self.connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.JOBS_TABLE} (
                {id_col},
                queue TEXT NOT NULL,
                payload TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                available_at TEXT NOT NULL,
                reserved_at TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.FAILED_TABLE} (
                {id_col},
                queue TEXT NOT NULL,
                payload TEXT NOT NULL,
                exception TEXT NOT NULL,
                failed_at TEXT NOT NULL
            )
            """
        )

    def _id_column_sql(self) -> str:
        name = type(self.connection).__name__.lower()
        if "postgres" in name:
            return "id SERIAL PRIMARY KEY"
        if "mysql" in name:
            return "id INTEGER PRIMARY KEY AUTO_INCREMENT"
        return "id INTEGER PRIMARY KEY AUTOINCREMENT"

    def push(self, job: Job, queue: str | None = None) -> None:
        name = queue or job.queue
        now = _utcnow()
        sql = (
            f"INSERT INTO {self.JOBS_TABLE} "
            f"(queue, payload, attempts, available_at, created_at) "
            f"VALUES ({self._ph}, {self._ph}, {self._ph}, {self._ph}, {self._ph})"
        )
        self.connection.execute(
            sql,
            (name, serialize_job(job, attempts=0), 0, now, now),
        )

    def pop(self, queue: str = "default") -> ReservedJob | None:
        now = _utcnow()
        select = (
            f"SELECT id, payload, attempts FROM {self.JOBS_TABLE} "
            f"WHERE queue = {self._ph} AND reserved_at IS NULL "
            f"AND available_at <= {self._ph} "
            f"ORDER BY id ASC LIMIT 1"
        )
        row = self.connection.fetch_one(select, (queue, now))
        if row is None:
            return None

        job_id = row["id"]
        update = (
            f"UPDATE {self.JOBS_TABLE} SET reserved_at = {self._ph}, "
            f"attempts = attempts + 1 WHERE id = {self._ph} "
            f"AND reserved_at IS NULL"
        )
        self.connection.execute(update, (now, job_id))
        # Re-read attempts after increment
        refreshed = self.connection.fetch_one(
            f"SELECT payload, attempts FROM {self.JOBS_TABLE} "
            f"WHERE id = {self._ph}",
            (job_id,),
        )
        if refreshed is None:
            return None
        try:
            job, meta = deserialize_job(refreshed["payload"])
        except Exception as error:
            raise DriverError(str(error)) from error
        return ReservedJob(
            job=job,
            attempts=int(refreshed["attempts"]),
            tries=int(meta["tries"]),
            queue=queue,
            receipt=job_id,
        )

    def ack(self, reserved: ReservedJob) -> None:
        self.connection.execute(
            f"DELETE FROM {self.JOBS_TABLE} WHERE id = {self._ph}",
            (reserved.receipt,),
        )

    def release(self, reserved: ReservedJob, delay: float = 0) -> None:
        # delay ignored for v1 simplicity beyond available_at = now
        now = _utcnow()
        payload = serialize_job(reserved.job, attempts=reserved.attempts)
        self.connection.execute(
            f"UPDATE {self.JOBS_TABLE} SET payload = {self._ph}, "
            f"reserved_at = NULL, available_at = {self._ph} "
            f"WHERE id = {self._ph}",
            (payload, now, reserved.receipt),
        )

    def fail(self, reserved: ReservedJob, error: BaseException) -> None:
        reserved.job.failed(error)
        now = _utcnow()
        payload = serialize_job(reserved.job, attempts=reserved.attempts)
        self.connection.execute(
            f"INSERT INTO {self.FAILED_TABLE} "
            f"(queue, payload, exception, failed_at) "
            f"VALUES ({self._ph}, {self._ph}, {self._ph}, {self._ph})",
            (reserved.queue, payload, repr(error), now),
        )
        self.ack(reserved)
