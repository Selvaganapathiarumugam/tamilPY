"""
MongoDB filter compilation for QueryBuilder (subset).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tpy.query.exceptions import GrammarError, InvalidOperatorError

if TYPE_CHECKING:
    from tpy.query.builder import QueryBuilder

_OP_MAP = {
    "=": "$eq",
    "!=": "$ne",
    ">": "$gt",
    ">=": "$gte",
    "<": "$lt",
    "<=": "$lte",
    "in": "$in",
    "not in": "$nin",
}


class MongoGrammar:
    """
    Compile QueryBuilder clauses into a Mongo filter document.

    Execution still goes through ``MongoProvider`` helpers when wired by
    callers; ``to_filter`` is the primary public compile API.
    """

    def __init__(self, connection: Any = None) -> None:
        self.connection = connection

    def to_filter(self, builder: QueryBuilder) -> dict[str, Any]:
        """Compile WHERE clauses into a MongoDB filter dict."""
        if builder.joins:
            raise GrammarError("MongoGrammar does not support SQL joins")
        if not builder.wheres:
            return {}
        and_parts: list[dict[str, Any]] = []
        or_parts: list[dict[str, Any]] = []
        for clause in builder.wheres:
            if clause.raw:
                raise GrammarError("MongoGrammar does not support where_raw")
            piece = self._clause(clause.column, clause.operator, clause.value)
            if clause.boolean == "or":
                or_parts.append(piece)
            else:
                and_parts.append(piece)
        if or_parts and and_parts:
            return {"$and": and_parts + [{"$or": or_parts}]}
        if or_parts:
            return {"$or": or_parts} if len(or_parts) > 1 else or_parts[0]
        if len(and_parts) == 1:
            return and_parts[0]
        return {"$and": and_parts} if and_parts else {}

    def _clause(self, column: str, operator: str, value: Any) -> dict[str, Any]:
        op = operator.lower()
        if op in {"is", "is not"}:
            exists = op == "is not"
            return {column: {"$eq": None}} if not exists else {
                column: {"$ne": None}
            }
        mongo_op = _OP_MAP.get(op)
        if mongo_op is None:
            raise InvalidOperatorError(operator)
        if op == "=":
            return {column: value}
        return {column: {mongo_op: value}}
