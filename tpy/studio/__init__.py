"""tamilPY Studio — local visual schema builder."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def studio_version() -> str:
    """Return the installed tamilPY version string."""
    try:
        return version("tamilPY")
    except PackageNotFoundError:
        from tpy import __version__

        return __version__
