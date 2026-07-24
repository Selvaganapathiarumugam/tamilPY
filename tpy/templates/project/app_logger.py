"""
Application logger.

Uses the TPY runtime logger and writes to ``storage/logs/app.log``.
"""

from tpy.runtime.logger import get_logger

logger = get_logger("app")
