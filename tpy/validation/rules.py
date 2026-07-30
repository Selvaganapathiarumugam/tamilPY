"""
Built-in validation rules.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any
from uuid import UUID


class Rule(ABC):
    """Single validation rule."""

    name: str = "rule"

    @abstractmethod
    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        """Return True when ``value`` is valid for ``attribute``."""

    def message(self, attribute: str, value: Any) -> str:
        """Default failure message."""
        return f"The {attribute} field is invalid."


class Required(Rule):
    name = "required"

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        return True

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field is required."


class Nullable(Rule):
    """Marker rule — empty values skip other rules."""

    name = "nullable"

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        return True


class Email(Rule):
    name = "email"
    _pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        return bool(self._pattern.match(str(value)))

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be a valid email address."


class StringRule(Rule):
    name = "string"

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        return isinstance(value, str)

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be a string."


class IntegerRule(Rule):
    name = "integer"

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        if isinstance(value, str) and value.lstrip("-").isdigit():
            return True
        return False

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be an integer."


class Numeric(Rule):
    name = "numeric"

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, bool):
            return False
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be numeric."


class BooleanRule(Rule):
    name = "boolean"
    _truthy = {True, "1", "true", "True", "yes", "on"}
    _falsy = {False, "0", "false", "False", "no", "off"}

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        return value in self._truthy or value in self._falsy

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be true or false."


class Min(Rule):
    name = "min"

    def __init__(self, limit: str) -> None:
        self.limit = float(limit)

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, str):
            return len(value) >= self.limit
        if isinstance(value, (list, dict)):
            return len(value) >= self.limit
        try:
            return float(value) >= self.limit
        except (TypeError, ValueError):
            return False

    def message(self, attribute: str, value: Any) -> str:
        if isinstance(value, str):
            limit = int(self.limit)
            return f"The {attribute} field must be at least {limit} characters."
        return f"The {attribute} field must be at least {self.limit}."


class Max(Rule):
    name = "max"

    def __init__(self, limit: str) -> None:
        self.limit = float(limit)

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, str):
            return len(value) <= self.limit
        if isinstance(value, (list, dict)):
            return len(value) <= self.limit
        try:
            return float(value) <= self.limit
        except (TypeError, ValueError):
            return False

    def message(self, attribute: str, value: Any) -> str:
        if isinstance(value, str):
            limit = int(self.limit)
            return (
                f"The {attribute} field must not be greater than {limit} characters."
            )
        return f"The {attribute} field must not be greater than {self.limit}."


class Between(Rule):
    name = "between"

    def __init__(self, bounds: str) -> None:
        low, high = bounds.split(",", 1)
        self.low = float(low)
        self.high = float(high)

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, str):
            return self.low <= len(value) <= self.high
        try:
            number = float(value)
            return self.low <= number <= self.high
        except (TypeError, ValueError):
            return False

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be between {self.low} and {self.high}."


class InRule(Rule):
    name = "in"

    def __init__(self, options: str) -> None:
        self.options = [part.strip() for part in options.split(",") if part.strip()]

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        return str(value) in self.options

    def message(self, attribute: str, value: Any) -> str:
        return f"The selected {attribute} is invalid."


class NotIn(Rule):
    name = "not_in"

    def __init__(self, options: str) -> None:
        self.options = [part.strip() for part in options.split(",") if part.strip()]

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        return str(value) not in self.options

    def message(self, attribute: str, value: Any) -> str:
        return f"The selected {attribute} is invalid."


class Confirmed(Rule):
    name = "confirmed"

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        return data.get(f"{attribute}_confirmation") == value

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} confirmation does not match."


class Regex(Rule):
    name = "regex"

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        return re.search(self.pattern, str(value)) is not None

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field format is invalid."


class UuidRule(Rule):
    name = "uuid"

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        try:
            UUID(str(value))
            return True
        except (ValueError, TypeError, AttributeError):
            return False

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be a valid UUID."


class Url(Rule):
    name = "url"
    _pattern = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        return bool(self._pattern.match(str(value)))

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be a valid URL."


class Same(Rule):
    name = "same"

    def __init__(self, other: str) -> None:
        self.other = other

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        return data.get(self.other) == value

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} and {self.other} fields must match."


class Different(Rule):
    name = "different"

    def __init__(self, other: str) -> None:
        self.other = other

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        return data.get(self.other) != value

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} and {self.other} fields must be different."


class ListRule(Rule):
    name = "list"

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        return isinstance(value, list)

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be a list."


class Size(Rule):
    name = "size"

    def __init__(self, size: str) -> None:
        self.size = float(size)

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        if value is None or value == "":
            return True
        if isinstance(value, str):
            return len(value) == self.size
        if isinstance(value, (list, dict)):
            return len(value) == self.size
        try:
            return float(value) == self.size
        except (TypeError, ValueError):
            return False

    def message(self, attribute: str, value: Any) -> str:
        return f"The {attribute} field must be {self.size}."


class ClosureRule(Rule):
    """Wrap a custom callable ``(attribute, value, data) -> bool``."""

    name = "closure"

    def __init__(
        self,
        name: str,
        callback: Callable[[str, Any, dict[str, Any]], bool],
        message_text: str | None = None,
    ) -> None:
        self.name = name
        self.callback = callback
        self.message_text = message_text

    def passes(self, attribute: str, value: Any, data: dict[str, Any]) -> bool:
        return bool(self.callback(attribute, value, data))

    def message(self, attribute: str, value: Any) -> str:
        return self.message_text or f"The {attribute} field is invalid."


RULE_BUILDERS: dict[str, Callable[..., Rule]] = {
    "required": lambda params="": Required(),
    "nullable": lambda params="": Nullable(),
    "email": lambda params="": Email(),
    "string": lambda params="": StringRule(),
    "integer": lambda params="": IntegerRule(),
    "numeric": lambda params="": Numeric(),
    "boolean": lambda params="": BooleanRule(),
    "min": lambda params: Min(params),
    "max": lambda params: Max(params),
    "between": lambda params: Between(params),
    "in": lambda params: InRule(params),
    "not_in": lambda params: NotIn(params),
    "confirmed": lambda params="": Confirmed(),
    "regex": lambda params: Regex(params),
    "uuid": lambda params="": UuidRule(),
    "url": lambda params="": Url(),
    "same": lambda params: Same(params),
    "different": lambda params: Different(params),
    "list": lambda params="": ListRule(),
    "array": lambda params="": ListRule(),
    "size": lambda params: Size(params),
}


def is_empty(value: Any) -> bool:
    """Return whether a value is considered empty for nullable skipping."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False
