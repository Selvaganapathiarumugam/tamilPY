"""
Kernel exceptions.
"""

from tpy.exceptions import TpyError


class KernelError(TpyError):
    """Base error for the application kernel."""


class BindingError(KernelError):
    """Raised when a container binding is missing or invalid."""


class ProviderError(KernelError):
    """Raised when a service provider fails."""


class PluginError(KernelError):
    """Raised when a plugin cannot be loaded or registered."""
