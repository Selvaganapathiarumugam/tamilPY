"""
Immutable clause dataclasses collected by ``QueryBuilder``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class WhereClause:
    """A single WHERE / HAVING predicate."""

    column: str
    operator: str
    value: Any
    boolean: str = "and"
    raw: bool = False


@dataclass(slots=True, frozen=True)
class JoinClause:
    """A JOIN clause."""

    join_type: str
    table: str
    first: str
    operator: str
    second: str


@dataclass(slots=True, frozen=True)
class OrderClause:
    """An ORDER BY clause."""

    column: str
    direction: str = "asc"


@dataclass(slots=True, frozen=True)
class AggregateClause:
    """An aggregate select expression."""

    function: str
    column: str
    alias: str | None = None
