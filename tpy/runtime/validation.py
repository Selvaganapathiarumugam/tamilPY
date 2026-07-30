"""
Legacy fluent validation helpers.

Prefer ``tpy.validation.Validator.make`` for rule-string validation.
"""

from collections.abc import Callable
from typing import Any


class ValidationError(Exception):
    """Raised when request validation fails (legacy dict[str, str] errors)."""

    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__("Validation failed")


class Validator:
    """
    Minimal fluent field validator (legacy runtime helper).

    Prefer ``tpy.validation.Validator.make`` for pipe-rule validation.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.errors: dict[str, str] = {}

    def required(self, *fields: str) -> "Validator":
        """Mark fields as required."""
        for name in fields:
            value = self.data.get(name)
            if value is None or value == "":
                self.errors[name] = "This field is required."
        return self

    def email(self, field: str) -> "Validator":
        """Validate a simple email format."""
        value = self.data.get(field)
        if value is not None and value != "" and "@" not in str(value):
            self.errors[field] = "Invalid email address."
        return self

    def validate(self) -> dict[str, Any]:
        """
        Return validated data or raise ``ValidationError``.

        Returns:
            Original data dict when valid.
        """
        if self.errors:
            raise ValidationError(self.errors)
        return self.data


def validate(
    data: dict[str, Any],
    rules: Callable[[Validator], Validator],
) -> dict[str, Any]:
    """
    Run legacy fluent validation rules against a data dict.

    For pipe-rule validation use ``tpy.validation.validate``.
    """
    validator = Validator(data)
    rules(validator)
    return validator.validate()
