from abc import ABC, abstractmethod

from tpy.database.column import Column


class Migration(ABC):
    """
    Base class for database migrations.

    Subclasses implement ``up`` and ``down``. Helper methods collect
    operations that providers later compile into SQL.
    """

    def __init__(self) -> None:
        self.operations: list[dict] = []

    @abstractmethod
    def up(self) -> None:
        """Apply the migration."""

    @abstractmethod
    def down(self) -> None:
        """Revert the migration."""

    def create_table(self, table_name: str) -> None:
        """Queue a create-table operation."""
        self.operations.append(
            {
                "action": "create_table",
                "table": table_name,
            }
        )

    def drop_table(self, table_name: str) -> None:
        """Queue a drop-table operation."""
        self.operations.append(
            {
                "action": "drop_table",
                "table": table_name,
            }
        )

    def column(self, name: str, datatype: str) -> Column:
        """
        Queue a column definition and return it for fluent constraints.

        Args:
            name: Column name.
            datatype: TPY datatype string.

        Returns:
            Column instance attached to this migration.
        """
        return self.add_column(Column(name, datatype))

    def add_column(self, column: Column) -> Column:
        """Queue an existing column definition."""
        self.operations.append(
            {
                "action": "column",
                "column": column,
            }
        )
        return column

    def string(self, name: str) -> Column:
        """Add a string column."""
        return self.add_column(Column(name, "string"))

    def integer(self, name: str) -> Column:
        """Add an integer column."""
        return self.add_column(Column(name, "integer"))

    def float(self, name: str) -> Column:
        """Add a float column."""
        return self.add_column(Column(name, "float"))

    def boolean(self, name: str) -> Column:
        """Add a boolean column."""
        return self.add_column(Column(name, "boolean"))

    def uuid(self, name: str) -> Column:
        """Add a UUID column."""
        return self.add_column(Column(name, "uuid"))

    def datetime(self, name: str) -> Column:
        """Add a datetime column."""
        return self.add_column(Column(name, "datetime"))
