"""
Base job type for background work.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Job(ABC):
    """
    Synchronous unit of work pushed onto a queue.

    Subclasses should keep constructor arguments JSON-serializable.
    """

    queue: str = "default"
    tries: int = 3

    @abstractmethod
    def handle(self) -> None:
        """Execute the job."""

    def failed(self, error: BaseException) -> None:
        """Hook invoked after the job exhausts all attempts."""
        return None

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize constructor state.

        Default: public instance attributes (no leading underscore).
        """
        return {
            key: value
            for key, value in vars(self).items()
            if not key.startswith("_")
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        """Rehydrate a job from ``to_dict`` output."""
        return cls(**data)
