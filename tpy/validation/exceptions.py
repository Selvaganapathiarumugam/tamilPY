"""
Validation exceptions.
"""

from __future__ import annotations

from tpy.exceptions import TpyError


class ValidationException(TpyError):
    """
    Raised when validation fails.

    ``errors`` maps field name → list of messages (Laravel-style).
    """

    def __init__(self, errors: dict[str, list[str]]) -> None:
        self.errors = {
            key: list(messages) for key, messages in errors.items() if messages
        }
        super().__init__("Validation failed")

    def first_messages(self) -> dict[str, str]:
        """Return one message per field (for simple API envelopes)."""
        return {
            key: messages[0]
            for key, messages in self.errors.items()
            if messages
        }

    def to_dict(self) -> dict[str, list[str]]:
        """Return the full error bag."""
        return dict(self.errors)
