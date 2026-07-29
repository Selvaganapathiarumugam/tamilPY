"""
Cache-layer exceptions.
"""

from tpy.exceptions import TpyError


class CacheError(TpyError):
    """Base error for the cache system."""


class CacheDriverError(CacheError):
    """Raised when a cache backend cannot be used."""
