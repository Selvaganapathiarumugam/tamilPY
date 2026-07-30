"""Convert ``ProgramNode`` to/from Studio JSON AST (no auth in schema)."""

from __future__ import annotations

from typing import Any

from tpy.parser.ast import (
    DatabaseNode,
    EnumNode,
    FieldNode,
    ForeignKeyNode,
    ModelNode,
    ProgramNode,
    RelationNode,
)


def to_json(program: ProgramNode) -> dict[str, Any]:
    """
    Convert a parsed program into the Studio JSON AST shape.

    Does not include ``auth`` — callers merge sidecar auth separately.
    """
    return {
        "database": (
            program.database.provider.lower()
            if program.database is not None
            else None
        ),
        "models": [_model_to_json(model) for model in program.models],
        "enums": [_enum_to_json(enum) for enum in program.enums],
    }


def from_json(payload: dict[str, Any]) -> ProgramNode:
    """Build a ``ProgramNode`` from Studio JSON (ignores ``auth`` if present)."""
    database = None
    raw_db = payload.get("database")
    if raw_db:
        database = DatabaseNode(provider=str(raw_db).lower())

    enums = [
        EnumNode(
            name=str(item["name"]),
            values=[str(v) for v in item.get("values", [])],
        )
        for item in payload.get("enums", [])
    ]
    models = [_model_from_json(item) for item in payload.get("models", [])]
    return ProgramNode(database=database, models=models, enums=enums)


def _enum_to_json(enum: EnumNode) -> dict[str, Any]:
    return {"name": enum.name, "values": list(enum.values)}


def _model_to_json(model: ModelNode) -> dict[str, Any]:
    return {
        "name": model.name,
        "fields": [_field_to_json(field) for field in model.fields],
        "unique_together": [list(cols) for cols in model.unique_together],
        "relations": [_relation_to_json(rel) for rel in model.relations],
    }


def _field_to_json(field: FieldNode) -> dict[str, Any]:
    return {
        "name": field.name,
        "type": field.datatype,
        "constraints": list(field.constraints),
        "default": field.default if field.has_default else None,
        "has_default": field.has_default,
        "enum_values": list(field.enum_values),
        "references": (
            _reference_to_json(field.reference)
            if field.reference is not None
            else None
        ),
    }


def _reference_to_json(reference: ForeignKeyNode) -> dict[str, Any]:
    return {
        "model": reference.model,
        "table": reference.table,
        "column": reference.column,
        "on_delete": reference.on_delete,
        "on_update": reference.on_update,
    }


def _relation_to_json(relation: RelationNode) -> dict[str, Any]:
    return {
        "kind": relation.kind,
        "model": relation.model,
        "name": relation.name,
        "foreign_key": relation.foreign_key,
        "local_key": relation.local_key,
        "through": relation.through,
        "pivot_foreign_key": relation.pivot_foreign_key,
        "pivot_related_key": relation.pivot_related_key,
    }


def _model_from_json(item: dict[str, Any]) -> ModelNode:
    return ModelNode(
        name=str(item["name"]),
        fields=[_field_from_json(f) for f in item.get("fields", [])],
        unique_together=[
            [str(c) for c in cols] for cols in item.get("unique_together", [])
        ],
        relations=[_relation_from_json(r) for r in item.get("relations", [])],
    )


def _field_from_json(item: dict[str, Any]) -> FieldNode:
    datatype = str(item.get("type") or item.get("datatype") or "string")
    has_default = bool(item.get("has_default", False))
    default = item.get("default") if has_default else None
    if "has_default" not in item and "default" in item and item["default"] is not None:
        has_default = True
        default = item["default"]

    reference = None
    raw_ref = item.get("references")
    if isinstance(raw_ref, dict):
        reference = ForeignKeyNode(
            model=str(raw_ref["model"]),
            table=str(raw_ref.get("table") or str(raw_ref["model"]).lower()),
            column=str(raw_ref.get("column") or "id"),
            on_delete=raw_ref.get("on_delete"),
            on_update=raw_ref.get("on_update"),
        )

    return FieldNode(
        name=str(item["name"]),
        datatype=datatype,
        constraints=[str(c) for c in item.get("constraints", [])],
        default=default,
        has_default=has_default,
        reference=reference,
        enum_values=[str(v) for v in item.get("enum_values", [])],
    )


def _relation_from_json(item: dict[str, Any]) -> RelationNode:
    return RelationNode(
        kind=str(item["kind"]),
        model=str(item["model"]),
        name=str(item["name"]),
        foreign_key=item.get("foreign_key"),
        local_key=item.get("local_key"),
        through=item.get("through"),
        pivot_foreign_key=item.get("pivot_foreign_key"),
        pivot_related_key=item.get("pivot_related_key"),
    )
