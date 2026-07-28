class Column:
    """
    Fluent column definition used inside migrations.
    """

    def __init__(self, name: str, datatype: str) -> None:
        self.name = name
        self.datatype = datatype
        self.options: dict = {}

    def primary(self) -> "Column":
        """Mark the column as a primary key."""
        self.options["primary"] = True
        return self

    def unique(self) -> "Column":
        """Mark the column as unique."""
        self.options["unique"] = True
        return self

    def nullable(self) -> "Column":
        """Allow NULL values."""
        self.options["nullable"] = True
        return self

    def index(self) -> "Column":
        """Request an index on the column."""
        self.options["index"] = True
        return self

    def references(
        self,
        table: str,
        column: str = "id",
        on_delete: str | None = None,
        on_update: str | None = None,
    ) -> "Column":
        """
        Add a foreign-key reference to ``table(column)``.

        Args:
            table: Referenced table name.
            column: Referenced column name (defaults to ``id``).
            on_delete: Optional ON DELETE action.
            on_update: Optional ON UPDATE action.
        """
        payload: dict = {
            "table": table,
            "column": column,
        }
        if on_delete:
            payload["on_delete"] = on_delete
        if on_update:
            payload["on_update"] = on_update
        self.options["references"] = payload
        return self

    def check(self, expression: str) -> "Column":
        """Attach a CHECK constraint expression."""
        self.options["check"] = expression
        return self

    def default(self, value) -> "Column":
        """Set a default value."""
        self.options["default"] = value
        return self

    def to_dict(self) -> dict:
        """Serialize the column definition."""
        return {
            "name": self.name,
            "datatype": self.datatype,
            "options": self.options,
        }
