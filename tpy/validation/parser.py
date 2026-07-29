"""
Parse pipe-delimited rule strings into Rule instances.
"""

from __future__ import annotations

from typing import Any, Callable

from tpy.validation.rules import RULE_BUILDERS, Rule


class UnknownRuleError(ValueError):
    """Raised when a rule name is not registered."""


def parse_rules(
    rules: str | list[Any],
    custom: dict[str, Any] | None = None,
) -> list[Rule]:
    """
    Parse ``\"required|email|min:3\"`` or a list of rule names / Rule objects.
    """
    if isinstance(rules, str):
        parts: list[Any] = [
            part.strip() for part in rules.split("|") if part.strip()
        ]
    else:
        parts = list(rules)

    parsed: list[Rule] = []
    for part in parts:
        if isinstance(part, Rule):
            parsed.append(part)
            continue
        name, _, params = str(part).partition(":")
        name = name.strip()
        params = params.strip()
        builder: Any = None
        if custom and name in custom:
            builder = custom[name]
        elif name in RULE_BUILDERS:
            builder = RULE_BUILDERS[name]
        else:
            raise UnknownRuleError(f"Unknown validation rule: {name}")

        if isinstance(builder, type) and issubclass(builder, Rule):
            instance = builder(params) if params else builder()
        else:
            # factory callable from RULE_BUILDERS or Validator.extend
            try:
                instance = builder(params) if params else builder()
            except TypeError:
                instance = builder(params)
        if not isinstance(instance, Rule):
            # extend() may register (callback, message) wrappers via ClosureRule
            raise UnknownRuleError(f"Rule factory for '{name}' did not return a Rule")
        parsed.append(instance)
    return parsed
