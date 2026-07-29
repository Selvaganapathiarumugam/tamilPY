"""
Registry mapping model name → named relation definitions.
"""

from __future__ import annotations

from tpy.query.exceptions import InvalidRelationError
from tpy.query.relations import RelationDefinition, build_relation


class RelationRegistry:
    """In-memory registry of ORM relations keyed by model name."""

    def __init__(self) -> None:
        self._definitions: dict[str, dict[str, RelationDefinition]] = {}

    def register(self, model: str, definition: RelationDefinition) -> None:
        """Register a relation for ``model``."""
        bucket = self._definitions.setdefault(model, {})
        bucket[definition.name] = definition

    def get(self, model: str, name: str):
        """Return a relation strategy for ``model.name``."""
        definition = self._definitions.get(model, {}).get(name)
        if definition is None:
            raise InvalidRelationError(name)
        return build_relation(definition)

    def has(self, model: str, name: str) -> bool:
        """Return whether a relation is registered."""
        return name in self._definitions.get(model, {})

    def definitions_for(self, model: str) -> dict[str, RelationDefinition]:
        """Return all relation definitions for a model."""
        return dict(self._definitions.get(model, {}))
