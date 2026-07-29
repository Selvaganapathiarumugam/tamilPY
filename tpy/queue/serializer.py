"""
Serialize / deserialize jobs for queue payloads.
"""

from __future__ import annotations

import importlib
import json
from typing import Any

from tpy.queue.exceptions import JobError
from tpy.queue.job import Job


def job_path(job: Job | type[Job]) -> str:
    """Return ``module:QualName`` for a job class or instance."""
    cls = job if isinstance(job, type) else type(job)
    return f"{cls.__module__}:{cls.__qualname__}"


def serialize_job(job: Job, attempts: int = 0) -> str:
    """Encode a job as a JSON payload string."""
    payload = {
        "job": job_path(job),
        "data": job.to_dict(),
        "attempts": attempts,
        "queue": job.queue,
        "tries": job.tries,
    }
    return json.dumps(payload)


def deserialize_job(raw: str) -> tuple[Job, dict[str, Any]]:
    """
    Decode a payload into a job instance and metadata.

    Returns:
        ``(job, meta)`` where meta includes attempts/tries/queue.
    """
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise JobError(f"Invalid job payload: {error}") from error

    path = payload.get("job")
    if not path or ":" not in path:
        raise JobError("Job payload missing 'job' import path")

    module_name, _, qualname = path.partition(":")
    try:
        module = importlib.import_module(module_name)
        attr: Any = module
        for part in qualname.split("."):
            attr = getattr(attr, part)
    except (ImportError, AttributeError) as error:
        raise JobError(f"Unable to import job '{path}': {error}") from error

    if not isinstance(attr, type) or not issubclass(attr, Job):
        raise JobError(f"'{path}' is not a Job subclass")

    data = payload.get("data") or {}
    try:
        job = attr.from_dict(data)
    except TypeError as error:
        raise JobError(f"Unable to rehydrate job '{path}': {error}") from error

    meta = {
        "attempts": int(payload.get("attempts", 0)),
        "tries": int(payload.get("tries", job.tries)),
        "queue": str(payload.get("queue", job.queue)),
        "raw": raw,
    }
    return job, meta
