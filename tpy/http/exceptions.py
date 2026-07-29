"""
HTTP-layer exceptions.
"""

from tpy.exceptions import TpyError


class HttpError(TpyError):
    """Base error for HTTP helpers."""
