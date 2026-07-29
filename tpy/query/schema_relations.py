"""
Build a ``RelationRegistry`` from a parsed ``ProgramNode``.
"""

from __future__ import annotations

from tpy.parser.ast import ModelNode, ProgramNode, RelationNode
from tpy.query.relation_registry import RelationRegistry
from tpy.query.relations import RelationDefinition


def registry_from_program(program: ProgramNode) -> RelationRegistry:
    """
    Convert schema AST relation blocks into a runtime registry.

    Args:
        program: Parsed ``schema.tpy`` AST.

    Returns:
        Populated ``RelationRegistry``.
    """
    models = {model.name: model for model in program.models}
    registry = RelationRegistry()
    for model in program.models:
        for relation in model.relations:
            definition = _to_definition(model, relation, models)
            registry.register(model.name, definition)
    return registry


def _to_definition(
    parent: ModelNode,
    relation: RelationNode,
    models: dict[str, ModelNode],
) -> RelationDefinition:
    related = models.get(relation.model)
    related_table = relation.model.lower()
    related_columns = None
    if related is not None:
        related_columns = frozenset(field.name for field in related.fields)

    foreign_key = relation.foreign_key
    local_key = relation.local_key or "id"
    through_table = None
    pivot_foreign_key = relation.pivot_foreign_key
    pivot_related_key = relation.pivot_related_key

    if relation.kind == "belongs_to":
        if foreign_key is None:
            foreign_key = f"{relation.model.lower()}_id"
    elif relation.kind in {"has_many", "has_one"}:
        if foreign_key is None:
            foreign_key = f"{parent.name.lower()}_id"
    elif relation.kind == "belongs_to_many":
        through_name = relation.through or ""
        through_table = through_name.lower()
        if pivot_foreign_key is None:
            pivot_foreign_key = f"{parent.name.lower()}_id"
        if pivot_related_key is None:
            pivot_related_key = f"{relation.model.lower()}_id"
        foreign_key = foreign_key or pivot_foreign_key

    return RelationDefinition(
        kind=relation.kind,
        name=relation.name,
        model=relation.model,
        related_table=related_table,
        foreign_key=foreign_key or "",
        local_key=local_key,
        through_table=through_table,
        pivot_foreign_key=pivot_foreign_key,
        pivot_related_key=pivot_related_key,
        related_columns=related_columns,
    )
