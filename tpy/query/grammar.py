"""
SQL dialect grammars that compile ``QueryBuilder`` state to SQL.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tpy.query.exceptions import GrammarError, InvalidOperatorError
from tpy.query.expression import Raw

if TYPE_CHECKING:
    from tpy.query.builder import QueryBuilder

_OPERATORS = {
    "=": "=",
    "!=": "!=",
    "<>": "<>",
    "<": "<",
    "<=": "<=",
    ">": ">",
    ">=": ">=",
    "like": "LIKE",
    "ilike": "ILIKE",
    "in": "IN",
    "not in": "NOT IN",
    "is": "IS",
    "is not": "IS NOT",
}


class Grammar:
    """Compile a QueryBuilder into dialect-specific SQL."""

    def __init__(self, connection: Any) -> None:
        self.connection = connection
        self.placeholder = getattr(connection, "PLACEHOLDER", "?")

    def quote(self, name: str) -> str:
        """Quote an identifier using the provider helper when available."""
        if "." in name:
            table, column = name.split(".", 1)
            return f"{self.quote(table)}.{self.quote(column)}"
        if hasattr(self.connection, "quote_identifier"):
            return self.connection.quote_identifier(name)
        escaped = name.replace('"', '""')
        return f'"{escaped}"'

    def compile_select(self, builder: QueryBuilder) -> tuple[str, list[Any]]:
        """Compile a SELECT statement."""
        columns = self._compile_columns(builder)
        table = self.quote(builder.table)
        sql = f"SELECT {columns} FROM {table}"
        params: list[Any] = []

        join_sql, join_params = self._compile_joins(builder)
        if join_sql:
            sql += f" {join_sql}"
            params.extend(join_params)

        where_sql, where_params = self._compile_wheres(builder.wheres)
        if where_sql:
            sql += f" WHERE {where_sql}"
            params.extend(where_params)

        if builder.groups:
            groups = ", ".join(self.quote(g) for g in builder.groups)
            sql += f" GROUP BY {groups}"

        having_sql, having_params = self._compile_wheres(builder.havings)
        if having_sql:
            sql += f" HAVING {having_sql}"
            params.extend(having_params)

        if builder.orders:
            parts = [
                f"{self.quote(o.column)} {o.direction.upper()}"
                for o in builder.orders
            ]
            sql += f" ORDER BY {', '.join(parts)}"

        if builder.limit_value is not None:
            sql += f" LIMIT {int(builder.limit_value)}"
        if builder.offset_value is not None:
            sql += f" OFFSET {int(builder.offset_value)}"

        return sql, params

    def compile_count(self, builder: QueryBuilder) -> tuple[str, list[Any]]:
        """Compile COUNT(*) with the same filters as the select."""
        clone = builder._clone()
        clone.columns = []
        clone.orders = []
        clone.limit_value = None
        clone.offset_value = None
        clone.aggregate = ("count", "*", "aggregate")
        return self.compile_select(clone)

    def compile_insert(
        self,
        builder: QueryBuilder,
        values: dict[str, Any],
    ) -> tuple[str, list[Any]]:
        """Compile an INSERT statement."""
        if not values:
            raise GrammarError("insert requires at least one column")
        table = self.quote(builder.table)
        cols = ", ".join(self.quote(k) for k in values)
        placeholders = ", ".join(self.placeholder for _ in values)
        sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        return sql, list(values.values())

    def compile_update(
        self,
        builder: QueryBuilder,
        values: dict[str, Any],
    ) -> tuple[str, list[Any]]:
        """Compile an UPDATE statement."""
        if not values:
            raise GrammarError("update requires at least one column")
        if not builder.wheres and not builder.allow_unfiltered_writes:
            raise GrammarError(
                "Refusing UPDATE without WHERE; call allow_unfiltered()"
            )
        table = self.quote(builder.table)
        assignments = ", ".join(
            f"{self.quote(k)} = {self.placeholder}" for k in values
        )
        sql = f"UPDATE {table} SET {assignments}"
        params: list[Any] = list(values.values())
        where_sql, where_params = self._compile_wheres(builder.wheres)
        if where_sql:
            sql += f" WHERE {where_sql}"
            params.extend(where_params)
        return sql, params

    def compile_delete(self, builder: QueryBuilder) -> tuple[str, list[Any]]:
        """Compile a DELETE statement."""
        if not builder.wheres and not builder.allow_unfiltered_writes:
            raise GrammarError(
                "Refusing DELETE without WHERE; call allow_unfiltered()"
            )
        table = self.quote(builder.table)
        sql = f"DELETE FROM {table}"
        params: list[Any] = []
        where_sql, where_params = self._compile_wheres(builder.wheres)
        if where_sql:
            sql += f" WHERE {where_sql}"
            params.extend(where_params)
        return sql, params

    def _compile_columns(self, builder: QueryBuilder) -> str:
        if builder.aggregate:
            func, column, alias = builder.aggregate
            if column == "*":
                expr = f"{func.upper()}(*)"
            else:
                expr = f"{func.upper()}({self.quote(column)})"
            if alias:
                return f"{expr} AS {self.quote(alias)}"
            return expr
        if not builder.columns:
            return "*"
        parts: list[str] = []
        for column in builder.columns:
            if isinstance(column, Raw):
                parts.append(column.sql)
            else:
                parts.append(self.quote(str(column)))
        return ", ".join(parts)

    def _compile_joins(self, builder: QueryBuilder) -> tuple[str, list[Any]]:
        if not builder.joins:
            return "", []
        parts: list[str] = []
        for join in builder.joins:
            parts.append(
                f"{join.join_type.upper()} JOIN {self.quote(join.table)} "
                f"ON {self.quote(join.first)} {join.operator} "
                f"{self.quote(join.second)}"
            )
        return " ".join(parts), []

    def _compile_wheres(self, wheres: list) -> tuple[str, list[Any]]:
        if not wheres:
            return "", []
        sql_parts: list[str] = []
        params: list[Any] = []
        for index, clause in enumerate(wheres):
            prefix = "" if index == 0 else f"{clause.boolean.upper()} "
            if clause.raw:
                sql_parts.append(f"{prefix}{clause.column}")
                if isinstance(clause.value, (list, tuple)):
                    params.extend(clause.value)
                elif clause.value is not None:
                    params.append(clause.value)
                continue

            op_key = clause.operator.lower()
            if op_key not in _OPERATORS:
                raise InvalidOperatorError(clause.operator)
            sql_op = _OPERATORS[op_key]

            if op_key in {"in", "not in"}:
                values = list(clause.value or [])
                if not values:
                    sql_parts.append(f"{prefix}1 = 0")
                    continue
                placeholders = ", ".join(self.placeholder for _ in values)
                sql_parts.append(
                    f"{prefix}{self.quote(clause.column)} {sql_op} "
                    f"({placeholders})"
                )
                params.extend(values)
                continue

            if op_key in {"is", "is not"}:
                sql_parts.append(
                    f"{prefix}{self.quote(clause.column)} {sql_op} NULL"
                )
                continue

            sql_parts.append(
                f"{prefix}{self.quote(clause.column)} {sql_op} "
                f"{self.placeholder}"
            )
            params.append(clause.value)

        return " ".join(sql_parts), params


class SqliteGrammar(Grammar):
    """SQLite SQL grammar (``?`` placeholders)."""


class PostgresGrammar(Grammar):
    """PostgreSQL SQL grammar (``%s`` placeholders)."""


class MysqlGrammar(Grammar):
    """MySQL SQL grammar (``%s`` placeholders, backtick quoting fallback)."""

    def quote(self, name: str) -> str:
        if "." in name:
            table, column = name.split(".", 1)
            return f"{self.quote(table)}.{self.quote(column)}"
        if hasattr(self.connection, "quote_identifier"):
            return self.connection.quote_identifier(name)
        escaped = name.replace("`", "``")
        return f"`{escaped}`"


def grammar_for(connection: Any) -> Grammar:
    """Pick a grammar from the provider class name / placeholder."""
    name = type(connection).__name__.lower()
    if "postgres" in name:
        return PostgresGrammar(connection)
    if "mysql" in name:
        return MysqlGrammar(connection)
    if "mongo" in name:
        raise GrammarError("Use MongoGrammar for MongoDB providers")
    return SqliteGrammar(connection)
