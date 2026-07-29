"""
Query-layer exception hierarchy for tamilPY.
"""

from tpy.exceptions import TpyError


class QueryError(TpyError):
    """Base error for Query Builder and relation loading failures."""


class InvalidColumnError(QueryError):
    """Raised when a query references a column outside the allowlist."""

    def __init__(self, column: str) -> None:
        self.column = column
        super().__init__(f"Invalid column: {column}")


class InvalidOperatorError(QueryError):
    """Raised when a where/having operator is not supported."""

    def __init__(self, operator: str) -> None:
        self.operator = operator
        super().__init__(f"Invalid operator: {operator}")


class GrammarError(QueryError):
    """Raised when a query cannot be compiled to SQL or Mongo."""


class PaginationError(QueryError):
    """Raised for invalid pagination arguments."""


class RelationError(QueryError):
    """Base error for ORM relationship failures."""


class InvalidRelationError(RelationError):
    """Raised when an unknown relation name is requested."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Unknown relation: {name}")


class RelationConfigError(RelationError):
    """Raised when a relation definition is incomplete or invalid."""


class EagerLoadDepthError(RelationError):
    """Raised when nested eager-load depth exceeds the allowed maximum."""


class PivotError(RelationError):
    """Raised for pivot attach/detach/sync failures."""
