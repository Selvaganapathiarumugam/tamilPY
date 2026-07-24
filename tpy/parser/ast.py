from dataclasses import dataclass, field


@dataclass(slots=True)
class DatabaseNode:
    provider: str


@dataclass(slots=True)
class FieldNode:
    name: str
    datatype: str
    constraints: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ModelNode:
    name: str
    fields: list[FieldNode] = field(default_factory=list)


@dataclass(slots=True)
class ProgramNode:
    database: DatabaseNode | None = None
    models: list[ModelNode] = field(default_factory=list)