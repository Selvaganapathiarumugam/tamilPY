"""
ORM relationship strategy classes for eager loading.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from tpy.query.builder import QueryBuilder
from tpy.query.exceptions import RelationConfigError


@dataclass(slots=True)
class RelationDefinition:
    """Runtime description of a single model relation."""

    kind: str
    name: str
    model: str
    related_table: str
    foreign_key: str
    local_key: str = "id"
    through_table: str | None = None
    pivot_foreign_key: str | None = None
    pivot_related_key: str | None = None
    related_columns: frozenset[str] | None = None


class Relation(ABC):
    """Load and nest related rows onto parent dictionaries."""

    def __init__(self, definition: RelationDefinition) -> None:
        self.definition = definition

    @abstractmethod
    def constrain(
        self,
        builder: QueryBuilder,
        parents: list[dict[str, Any]],
    ) -> QueryBuilder:
        """Constrain a related query to the given parents."""

    @abstractmethod
    def match(
        self,
        parents: list[dict[str, Any]],
        related: list[dict[str, Any]],
        pivot_rows: list[dict[str, Any]] | None = None,
    ) -> None:
        """Attach related rows onto parents in place."""

    def parent_keys(self, parents: list[dict[str, Any]], key: str) -> list[Any]:
        """Collect non-null parent key values."""
        values: list[Any] = []
        for parent in parents:
            value = parent.get(key)
            if value is not None:
                values.append(value)
        return values


class BelongsTo(Relation):
    """Parent holds FK pointing at related PK."""

    def constrain(self, builder: QueryBuilder, parents: list[dict[str, Any]]):
        keys = self.parent_keys(parents, self.definition.foreign_key)
        return builder.where_in(self.definition.local_key, keys)

    def match(self, parents, related, pivot_rows=None) -> None:
        index = {
            row.get(self.definition.local_key): row for row in related
        }
        for parent in parents:
            parent[self.definition.name] = index.get(
                parent.get(self.definition.foreign_key)
            )


class HasMany(Relation):
    """Related rows hold FK pointing at parent PK."""

    def constrain(self, builder: QueryBuilder, parents: list[dict[str, Any]]):
        keys = self.parent_keys(parents, self.definition.local_key)
        return builder.where_in(self.definition.foreign_key, keys)

    def match(self, parents, related, pivot_rows=None) -> None:
        buckets: dict[Any, list] = {}
        for row in related:
            buckets.setdefault(row.get(self.definition.foreign_key), []).append(
                row
            )
        for parent in parents:
            parent[self.definition.name] = list(
                buckets.get(parent.get(self.definition.local_key), [])
            )


class HasOne(HasMany):
    """Same as has_many but nests a single row or None."""

    def match(self, parents, related, pivot_rows=None) -> None:
        super().match(parents, related, pivot_rows)
        for parent in parents:
            rows = parent.get(self.definition.name) or []
            parent[self.definition.name] = rows[0] if rows else None


class BelongsToMany(Relation):
    """Many-to-many via an explicit pivot table."""

    def constrain(self, builder: QueryBuilder, parents: list[dict[str, Any]]):
        return builder

    def match(self, parents, related, pivot_rows=None) -> None:
        if pivot_rows is None:
            raise RelationConfigError("belongs_to_many requires pivot rows")
        defn = self.definition
        related_index = {row.get("id"): row for row in related}
        mapping: dict[Any, list] = {}
        for pivot in pivot_rows:
            parent_id = pivot.get(defn.pivot_foreign_key)
            related_id = pivot.get(defn.pivot_related_key)
            item = related_index.get(related_id)
            if item is not None:
                mapping.setdefault(parent_id, []).append(item)
        for parent in parents:
            parent[defn.name] = list(
                mapping.get(parent.get(defn.local_key), [])
            )


def build_relation(definition: RelationDefinition) -> Relation:
    """Factory for relation strategy instances."""
    kind = definition.kind
    if kind == "belongs_to":
        return BelongsTo(definition)
    if kind == "has_many":
        return HasMany(definition)
    if kind == "has_one":
        return HasOne(definition)
    if kind == "belongs_to_many":
        if not definition.through_table:
            raise RelationConfigError(
                f"belongs_to_many '{definition.name}' requires through table"
            )
        return BelongsToMany(definition)
    raise RelationConfigError(f"Unknown relation kind: {kind}")
