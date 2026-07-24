from typing import Any, Callable


class ValidationError(Exception):
    """Raised when request validation fails."""

    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__("Validation failed")


class Validator:
    """
    Minimal field validator used by runtime helpers.
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
        if value is not None and "@" not in str(value):
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
    Run validation rules against a data dict.

    Args:
        data: Input payload.
        rules: Callable that configures a ``Validator``.

    Returns:
        Validated data.
    """
    validator = Validator(data)
    rules(validator)
    return validator.validate()
