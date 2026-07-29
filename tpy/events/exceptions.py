"""
Event system exceptions.
"""

from tpy.exceptions import TpyError


class EventError(TpyError):
    """Base error for the event / listener system."""
