"""
Eager-load related rows onto parent query results.
"""

from __future__ import annotations

from typing import Any

from tpy.query.builder import QueryBuilder
from tpy.query.exceptions import EagerLoadDepthError
from tpy.query.relation_registry import RelationRegistry
from tpy.query.relations import BelongsToMany, RelationDefinition

_DEFAULT_MAX_DEPTH = 3


class EagerLoader:
    """Batch-load relations with ``WHERE IN`` to avoid N+1 queries."""

    def __init__(
        self,
        registry: RelationRegistry,
        connection: Any,
        max_depth: int = _DEFAULT_MAX_DEPTH,
    ) -> None:
        self.registry = registry
        self.connection = connection
        self.max_depth = max_depth

    def load(
        self,
        rows: list[dict[str, Any]],
        relations: list[str],
        model: str,
        depth: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Eager-load ``relations`` onto ``rows`` for ``model``.

        Supports dot nesting: ``comments.author``.
        """
        if not rows or not relations:
            return rows
        if depth >= self.max_depth:
            raise EagerLoadDepthError(
                f"Eager load depth exceeded ({self.max_depth})"
            )

        groups: dict[str, list[str]] = {}
        for path in relations:
            head, _, tail = path.partition(".")
            groups.setdefault(head, [])
            if tail:
                groups[head].append(tail)

        for name, nested in groups.items():
            relation = self.registry.get(model, name)
            definition: RelationDefinition = relation.definition
            related_rows, pivot_rows = self._fetch_related(
                relation, rows, definition
            )
            relation.match(rows, related_rows, pivot_rows)

            if nested:
                children: list[dict[str, Any]] = []
                for parent in rows:
                    value = parent.get(name)
                    if value is None:
                        continue
                    if isinstance(value, list):
                        children.extend(value)
                    else:
                        children.append(value)
                self.load(
                    children,
                    nested,
                    definition.model,
                    depth=depth + 1,
                )
        return rows

    def _fetch_related(
        self,
        relation,
        parents: list[dict[str, Any]],
        definition: RelationDefinition,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None]:
        if isinstance(relation, BelongsToMany):
            return self._fetch_belongs_to_many(relation, parents, definition)

        builder = QueryBuilder(
            self.connection,
            definition.related_table,
            columns=definition.related_columns,
        )
        constrained = relation.constrain(builder, parents)
        return constrained.get(), None

    def _fetch_belongs_to_many(
        self,
        relation,
        parents: list[dict[str, Any]],
        definition: RelationDefinition,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        parent_ids = relation.parent_keys(parents, definition.local_key)
        if not parent_ids or not definition.through_table:
            return [], []

        pivot_fk = definition.pivot_foreign_key or ""
        pivot_rk = definition.pivot_related_key or ""
        pivot_rows = (
            QueryBuilder(self.connection, definition.through_table)
            .where_in(pivot_fk, parent_ids)
            .get()
        )
        related_ids = [
            row.get(pivot_rk)
            for row in pivot_rows
            if row.get(pivot_rk) is not None
        ]
        if not related_ids:
            return [], pivot_rows

        related = (
            QueryBuilder(
                self.connection,
                definition.related_table,
                columns=definition.related_columns,
            )
            .where_in("id", related_ids)
            .get()
        )
        return related, pivot_rows
