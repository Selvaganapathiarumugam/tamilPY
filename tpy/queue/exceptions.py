"""
Queue-layer exceptions.
"""

from tpy.exceptions import TpyError


class QueueError(TpyError):
    """Base error for queue / job failures."""


class JobError(QueueError):
    """Raised when a job cannot be (de)serialized or executed."""


class DriverError(QueueError):
    """Raised for queue driver / backend failures."""
