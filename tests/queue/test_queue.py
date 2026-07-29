"""Tests for sync and database queue drivers."""

from __future__ import annotations

from pathlib import Path

import pytest

from tpy.providers.sqlite.provider import SQLiteProvider
from tpy.queue import (
    DatabaseQueueDriver,
    Job,
    JobError,
    Queue,
    SyncQueueDriver,
    Worker,
)
from tpy.queue.serializer import deserialize_job, serialize_job


class RecordingJob(Job):
    """Job used in tests; records handled ids on the class."""

    handled: list[str] = []
    failed_ids: list[str] = []
    tries = 2

    def __init__(self, item_id: str, fail: bool = False) -> None:
        self.item_id = item_id
        self.fail = fail

    def handle(self) -> None:
        if self.fail:
            raise RuntimeError(f"boom:{self.item_id}")
        type(self).handled.append(self.item_id)

    def failed(self, error: BaseException) -> None:
        type(self).failed_ids.append(self.item_id)

    def to_dict(self) -> dict:
        return {"item_id": self.item_id, "fail": self.fail}


@pytest.fixture(autouse=True)
def _reset_recording_job():
    RecordingJob.handled = []
    RecordingJob.failed_ids = []
    yield
    RecordingJob.handled = []
    RecordingJob.failed_ids = []


def test_sync_driver_runs_inline():
    queue = Queue(SyncQueueDriver())
    queue.push(RecordingJob("a"))
    assert RecordingJob.handled == ["a"]


def test_serialize_roundtrip():
    raw = serialize_job(RecordingJob("x", fail=False), attempts=1)
    job, meta = deserialize_job(raw)
    assert isinstance(job, RecordingJob)
    assert job.item_id == "x"
    assert meta["attempts"] == 1


def test_deserialize_rejects_bad_payload():
    with pytest.raises(JobError):
        deserialize_job("{")


def test_database_driver_push_pop_ack(tmp_path: Path):
    db = SQLiteProvider(database_url=f"sqlite:///{tmp_path / 'q.sqlite3'}")
    db.connect()
    driver = DatabaseQueueDriver(db)
    driver.ensure_tables()
    queue = Queue(driver)
    queue.push(RecordingJob("db1"))

    reserved = queue.pop("default")
    assert reserved is not None
    assert reserved.job.item_id == "db1"
    reserved.job.handle()
    driver.ack(reserved)
    assert queue.pop("default") is None
    db.close()


def test_worker_retries_then_fails(tmp_path: Path):
    db = SQLiteProvider(database_url=f"sqlite:///{tmp_path / 'q2.sqlite3'}")
    db.connect()
    driver = DatabaseQueueDriver(db)
    driver.ensure_tables()
    queue = Queue(driver)
    queue.push(RecordingJob("bad", fail=True))

    worker = Worker(queue, once=True, sleep=0)
    # First attempt
    assert worker.run() == 1
    # Second attempt then fail (tries=2)
    assert worker.run() == 1
    assert RecordingJob.failed_ids == ["bad"]
    assert queue.pop("default") is None

    failed = db.fetch_one("SELECT queue FROM _tpy_failed_jobs LIMIT 1")
    assert failed is not None
    db.close()


def test_redis_driver_import_error_message():
    from tpy.queue.drivers.redis import RedisQueueDriver
    from tpy.queue.exceptions import DriverError

    # If redis isn't installed, constructor should explain the extra.
    try:
        import redis  # noqa: F401
    except ImportError:
        with pytest.raises(DriverError, match="tamilPY\\[redis\\]"):
            RedisQueueDriver()
