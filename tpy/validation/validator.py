"""
Advanced rule-based validator.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tpy.validation.exceptions import ValidationException
from tpy.validation.parser import parse_rules
from tpy.validation.rules import ClosureRule, Nullable, Rule, is_empty


class Validator:
    """
    Laravel-style validator driven by rule strings.

    Example::

        v = Validator.make(data, {"email": "required|email"})
        if v.fails():
            raise ValidationException(v.errors)
        return v.validated()
    """

    _custom_rules: dict[str, Any] = {}

    def __init__(
        self,
        data: dict[str, Any],
        rules: dict[str, str | list[Any]],
        messages: dict[str, str] | None = None,
    ) -> None:
        self.data = data
        self.rules = rules
        self.custom_messages = messages or {}
        self.errors: dict[str, list[str]] = {}
        self._validated: dict[str, Any] | None = None

    @classmethod
    def make(
        cls,
        data: dict[str, Any],
        rules: dict[str, str | list[Any]],
        messages: dict[str, str] | None = None,
    ) -> Validator:
        """Create a validator instance."""
        return cls(data, rules, messages)

    @classmethod
    def extend(
        cls,
        name: str,
        callback: Callable[[str, Any, dict[str, Any]], bool],
        message: str | None = None,
    ) -> None:
        """
        Register a custom rule name.

        ``callback(attribute, value, data) -> bool``.
        """

        def factory(params: str = "") -> Rule:
            _ = params
            return ClosureRule(name, callback, message)

        cls._custom_rules[name] = factory

    def passes(self) -> bool:
        """Run validation and return True when valid."""
        self._run()
        return not self.errors

    def fails(self) -> bool:
        """Run validation and return True when invalid."""
        return not self.passes()

    def validate(self) -> dict[str, Any]:
        """
        Validate and return data, or raise ``ValidationException``.
        """
        if self.fails():
            raise ValidationException(self.errors)
        return self.validated()

    def validated(self) -> dict[str, Any]:
        """
        Return only fields present in the rule set.

        Raises:
            ValidationException: When validation has not passed.
        """
        if self._validated is None:
            if self.fails():
                raise ValidationException(self.errors)
        assert self._validated is not None
        return dict(self._validated)

    def first_messages(self) -> dict[str, str]:
        """One message per failing field."""
        return {
            key: messages[0]
            for key, messages in self.errors.items()
            if messages
        }

    def _run(self) -> None:
        self.errors = {}
        validated: dict[str, Any] = {}
        for attribute, rule_spec in self.rules.items():
            rule_list = parse_rules(rule_spec, custom=self._custom_rules)
            value = self.data.get(attribute)
            nullable = any(isinstance(rule, Nullable) for rule in rule_list)

            if nullable and is_empty(value):
                validated[attribute] = value
                continue

            failed = False
            for rule in rule_list:
                if isinstance(rule, Nullable):
                    continue
                if not rule.passes(attribute, value, self.data):
                    message = self._message_for(attribute, rule, value)
                    self.errors.setdefault(attribute, []).append(message)
                    failed = True
                    break  # stop at first failing rule per field
            if not failed:
                validated[attribute] = value
        self._validated = validated if not self.errors else None

    def _message_for(self, attribute: str, rule: Rule, value: Any) -> str:
        key = f"{attribute}.{rule.name}"
        if key in self.custom_messages:
            return self.custom_messages[key]
        if attribute in self.custom_messages:
            return self.custom_messages[attribute]
        if rule.name in self.custom_messages:
            return self.custom_messages[rule.name]
        return rule.message(attribute, value)


def validate(
    data: dict[str, Any],
    rules: dict[str, str | list[Any]],
    messages: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Shortcut for ``Validator.make(...).validate()``."""
    return Validator.make(data, rules, messages).validate()
