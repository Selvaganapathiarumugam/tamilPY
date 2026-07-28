from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DatabaseNode:
    provider: str


@dataclass(slots=True)
class ForeignKeyNode:
    """A foreign key reference to another model's column."""

    model: str
    table: str
    column: str = "id"
    on_delete: str | None = None
    on_update: str | None = None


@dataclass(slots=True)
class FieldNode:
    name: str
    datatype: str
    constraints: list[str] = field(default_factory=list)
    default: Any = None
    has_default: bool = False
    reference: ForeignKeyNode | None = None
    enum_values: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EnumNode:
    """Named enum declaration: ``enum Status { draft published }``."""

    name: str
    values: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ModelNode:
    name: str
    fields: list[FieldNode] = field(default_factory=list)
    unique_together: list[list[str]] = field(default_factory=list)


@dataclass(slots=True)
class ProgramNode:
    database: DatabaseNode | None = None
    models: list[ModelNode] = field(default_factory=list)
    enums: list[EnumNode] = field(default_factory=list)
