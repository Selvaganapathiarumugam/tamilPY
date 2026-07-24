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
