"""
Fluent Query Builder executed through tamilPY database providers.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from tpy.query.clause import JoinClause, OrderClause, WhereClause
from tpy.query.exceptions import (
    InvalidColumnError,
    PaginationError,
    QueryError,
)
from tpy.query.expression import Raw
from tpy.query.grammar import Grammar, grammar_for
from tpy.query.paginator import LengthAwarePaginator

_MAX_PER_PAGE = 100


class QueryBuilder:
    """
    Sync fluent query builder.

    Compiles to parameterized SQL (or Mongo) and executes via a provider
    exposing ``fetch_all`` / ``fetch_one`` / ``execute``.
    """

    def __init__(
        self,
        connection: Any,
        table: str,
        columns: frozenset[str] | None = None,
        grammar: Grammar | None = None,
        relation_registry: Any | None = None,
        model: str | None = None,
    ) -> None:
        self.connection = connection
        self.table = table
        self.allowed_columns = columns
        self.grammar = grammar or grammar_for(connection)
        self.relation_registry = relation_registry
        self.model = model or table

        self.columns: list[str | Raw] = []
        self.wheres: list[WhereClause] = []
        self.havings: list[WhereClause] = []
        self.joins: list[JoinClause] = []
        self.orders: list[OrderClause] = []
        self.groups: list[str] = []
        self.limit_value: int | None = None
        self.offset_value: int | None = None
        self.aggregate: tuple[str, str, str | None] | None = None
        self.allow_unfiltered_writes = False
        self.eager_relations: list[str] = []

    def _clone(self) -> QueryBuilder:
        clone = QueryBuilder(
            self.connection,
            self.table,
            self.allowed_columns,
            self.grammar,
            self.relation_registry,
            self.model,
        )
        clone.columns = list(self.columns)
        clone.wheres = list(self.wheres)
        clone.havings = list(self.havings)
        clone.joins = list(self.joins)
        clone.orders = list(self.orders)
        clone.groups = list(self.groups)
        clone.limit_value = self.limit_value
        clone.offset_value = self.offset_value
        clone.aggregate = self.aggregate
        clone.allow_unfiltered_writes = self.allow_unfiltered_writes
        clone.eager_relations = list(self.eager_relations)
        return clone

    def _guard_column(self, column: str) -> None:
        if self.allowed_columns is None:
            return
        # Allow table.column for joins
        bare = column.split(".")[-1]
        if bare not in self.allowed_columns and column not in self.allowed_columns:
            raise InvalidColumnError(column)

    def select(self, *columns: str | Raw) -> QueryBuilder:
        """Set the SELECT column list."""
        clone = self._clone()
        clone.columns = []
        for column in columns:
            if isinstance(column, Raw):
                clone.columns.append(column)
            else:
                self._guard_column(column)
                clone.columns.append(column)
        return clone

    def where(
        self,
        column: str,
        operator: Any = None,
        value: Any = ...,
        boolean: str = "and",
    ) -> QueryBuilder:
        """Add a WHERE predicate. ``where("col", value)`` implies ``=``."""
        if value is ...:
            value = operator
            operator = "="
        self._guard_column(column)
        clone = self._clone()
        clone.wheres.append(
            WhereClause(
                column=column,
                operator=str(operator),
                value=value,
                boolean=boolean,
            )
        )
        return clone

    def or_where(
        self,
        column: str,
        operator: Any = None,
        value: Any = ...,
    ) -> QueryBuilder:
        """Add an OR WHERE predicate."""
        return self.where(column, operator, value, boolean="or")

    def where_in(self, column: str, values: Sequence[Any]) -> QueryBuilder:
        """Add ``WHERE column IN (...)``."""
        return self.where(column, "in", list(values))

    def where_null(self, column: str) -> QueryBuilder:
        """Add ``WHERE column IS NULL``."""
        return self.where(column, "is", None)

    def where_not_null(self, column: str) -> QueryBuilder:
        """Add ``WHERE column IS NOT NULL``."""
        return self.where(column, "is not", None)

    def where_raw(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
        boolean: str = "and",
    ) -> QueryBuilder:
        """Add a raw WHERE fragment with bind parameters."""
        clone = self._clone()
        clone.wheres.append(
            WhereClause(
                column=sql,
                operator="",
                value=list(params or ()),
                boolean=boolean,
                raw=True,
            )
        )
        return clone

    def join(
        self,
        table: str,
        first: str,
        operator: str,
        second: str,
        join_type: str = "inner",
    ) -> QueryBuilder:
        """Add a JOIN clause."""
        clone = self._clone()
        clone.joins.append(
            JoinClause(join_type, table, first, operator, second)
        )
        return clone

    def left_join(
        self,
        table: str,
        first: str,
        operator: str,
        second: str,
    ) -> QueryBuilder:
        """Add a LEFT JOIN clause."""
        return self.join(table, first, operator, second, join_type="left")

    def order_by(self, column: str, direction: str = "asc") -> QueryBuilder:
        """Add an ORDER BY clause."""
        self._guard_column(column)
        direction = direction.lower()
        if direction not in {"asc", "desc"}:
            raise QueryError(f"Invalid order direction: {direction}")
        clone = self._clone()
        clone.orders.append(OrderClause(column, direction))
        return clone

    def group_by(self, *columns: str) -> QueryBuilder:
        """Add GROUP BY columns."""
        clone = self._clone()
        for column in columns:
            self._guard_column(column)
            clone.groups.append(column)
        return clone

    def having(
        self,
        column: str,
        operator: Any = None,
        value: Any = ...,
    ) -> QueryBuilder:
        """Add a HAVING predicate."""
        if value is ...:
            value = operator
            operator = "="
        clone = self._clone()
        clone.havings.append(
            WhereClause(column=column, operator=str(operator), value=value)
        )
        return clone

    def limit(self, value: int) -> QueryBuilder:
        """Limit the number of returned rows."""
        clone = self._clone()
        clone.limit_value = int(value)
        return clone

    def offset(self, value: int) -> QueryBuilder:
        """Offset the result set."""
        clone = self._clone()
        clone.offset_value = int(value)
        return clone

    def allow_unfiltered(self) -> QueryBuilder:
        """Permit UPDATE/DELETE without a WHERE clause."""
        clone = self._clone()
        clone.allow_unfiltered_writes = True
        return clone

    def with_(self, *relations: str) -> QueryBuilder:
        """Eager-load named relations after fetching parent rows."""
        clone = self._clone()
        clone.eager_relations = list(self.eager_relations) + list(relations)
        return clone

    def to_sql(self) -> tuple[str, list[Any]]:
        """Compile the current SELECT without executing."""
        return self.grammar.compile_select(self)

    def get(self) -> list[dict[str, Any]]:
        """Execute SELECT and return all rows."""
        sql, params = self.grammar.compile_select(self)
        rows = self.connection.fetch_all(sql, params)
        return self._eager(rows)

    def first(self) -> dict[str, Any] | None:
        """Execute SELECT and return the first row."""
        rows = self.limit(1).get()
        return rows[0] if rows else None

    def find(self, record_id: Any, key: str = "id") -> dict[str, Any] | None:
        """Find a single row by primary key."""
        return self.where(key, record_id).first()

    def exists(self) -> bool:
        """Return whether any row matches."""
        return self.count() > 0

    def count(self) -> int:
        """Return COUNT(*) for the current filters."""
        sql, params = self.grammar.compile_count(self)
        row = self.connection.fetch_one(sql, params)
        if row is None:
            return 0
        value = row.get("aggregate", next(iter(row.values()), 0))
        return int(value or 0)

    def paginate(
        self,
        page: int = 1,
        per_page: int = 15,
    ) -> LengthAwarePaginator:
        """Return a length-aware page of results."""
        if page < 1:
            raise PaginationError("page must be >= 1")
        if per_page < 1 or per_page > _MAX_PER_PAGE:
            raise PaginationError(
                f"per_page must be between 1 and {_MAX_PER_PAGE}"
            )
        total = self.count()
        items = (
            self.offset((page - 1) * per_page)
            .limit(per_page)
            .get()
        )
        return LengthAwarePaginator(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
        )

    def insert(self, values: dict[str, Any]) -> None:
        """Insert a single row."""
        payload = self._filter_payload(values)
        sql, params = self.grammar.compile_insert(self, payload)
        self.connection.execute(sql, params)

    def update(self, values: dict[str, Any]) -> None:
        """Update matching rows."""
        payload = self._filter_payload(values, writable_only=True)
        sql, params = self.grammar.compile_update(self, payload)
        self.connection.execute(sql, params)

    def delete(self) -> None:
        """Delete matching rows."""
        sql, params = self.grammar.compile_delete(self)
        self.connection.execute(sql, params)

    def _filter_payload(
        self,
        values: dict[str, Any],
        writable_only: bool = False,
    ) -> dict[str, Any]:
        if self.allowed_columns is None:
            return dict(values)
        return {
            key: value
            for key, value in values.items()
            if key in self.allowed_columns
        }

    def _eager(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.eager_relations:
            return rows
        if self.relation_registry is None:
            raise QueryError(
                "with_() requires a relation_registry on QueryBuilder"
            )
        from tpy.query.eager import EagerLoader

        loader = EagerLoader(self.relation_registry, self.connection)
        return loader.load(rows, self.eager_relations, self.model)
