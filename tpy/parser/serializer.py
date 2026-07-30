"""Deterministic ``schema.tpy`` serializer from ``ProgramNode``."""

from __future__ import annotations

from typing import Any

from tpy.parser.ast import (
    EnumNode,
    FieldNode,
    ForeignKeyNode,
    ModelNode,
    ProgramNode,
    RelationNode,
)


def serialize_schema(program: ProgramNode) -> str:
    """
    Emit canonical ``schema.tpy`` source for ``program``.

    Field constraint order is preserved. Output always ends with a newline
    and uses ``\\n`` line endings only.
    """
    chunks: list[str] = []

    if program.database is not None:
        chunks.append(f"database {program.database.provider.lower()}")

    for enum in program.enums:
        if chunks:
            chunks.append("")
        chunks.append(_serialize_enum(enum))

    for model in program.models:
        if chunks:
            chunks.append("")
        chunks.append(_serialize_model(model))

    text = "\n".join(chunks)
    if text and not text.endswith("\n"):
        text += "\n"
    elif not text:
        text = "\n"
    return text


def _serialize_enum(enum: EnumNode) -> str:
    lines = [f"enum {enum.name} {{"]
    for value in enum.values:
        lines.append(f"  {value}")
    lines.append("}")
    return "\n".join(lines)


def _serialize_model(model: ModelNode) -> str:
    lines = [f"model {model.name} {{"]
    for field in model.fields:
        lines.append(f"  {_serialize_field(field)}")
    for columns in model.unique_together:
        joined = ", ".join(columns)
        lines.append(f"  unique({joined})")
    if model.relations:
        lines.append("  relations {")
        for relation in model.relations:
            lines.append(f"    {_serialize_relation(relation)}")
        lines.append("  }")
    lines.append("}")
    return "\n".join(lines)


def _serialize_field(field: FieldNode) -> str:
    parts = [f"{field.name}:", _serialize_datatype(field)]
    parts.extend(field.constraints)
    if field.has_default:
        parts.append("default")
        parts.append(_serialize_default(field.default))
    if field.reference is not None:
        parts.extend(_serialize_reference(field.reference))
    return " ".join(parts)


def _serialize_datatype(field: FieldNode) -> str:
    if field.datatype == "enum":
        values = ", ".join(field.enum_values)
        return f"enum({values})"
    if field.datatype.startswith("enum:"):
        return f"enum {field.datatype.split(':', 1)[1]}"
    return field.datatype


def _serialize_default(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def _serialize_reference(reference: ForeignKeyNode) -> list[str]:
    parts: list[str] = []
    if reference.column == "id":
        parts.append(f"references {reference.model}")
    else:
        parts.append(f"references {reference.model}.{reference.column}")
    if reference.on_delete:
        parts.append(f"on_delete {reference.on_delete}")
    if reference.on_update:
        parts.append(f"on_update {reference.on_update}")
    return parts


def _serialize_relation(relation: RelationNode) -> str:
    parts = [relation.kind, relation.model, "as", relation.name]
    if relation.foreign_key:
        parts.extend(["via", relation.foreign_key])
    if relation.through:
        parts.extend(["through", relation.through])
    return " ".join(parts)
