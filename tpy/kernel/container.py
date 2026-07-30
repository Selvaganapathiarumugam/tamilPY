"""
Simple dependency injection container.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from tpy.kernel.exceptions import BindingError

T = TypeVar("T")
Factory = Callable[["Container"], Any]


class Container:
    """
    Sync service container.

    Supports instance bindings, factories, and singletons.
    """

    def __init__(self) -> None:
        self._bindings: dict[str, Factory] = {}
        self._singletons: dict[str, bool] = {}
        self._instances: dict[str, Any] = {}
        self._aliases: dict[str, str] = {}

    def bind(
        self,
        abstract: str | type,
        concrete: Factory | Any,
        *,
        shared: bool = False,
    ) -> Container:
        """
        Bind ``abstract`` to a factory or concrete instance.

        Args:
            abstract: Service key (string or type; types use ``qualname`` path).
            concrete: Callable ``(container) -> service`` or a ready instance.
            shared: When True, resolve once and cache (singleton).
        """
        key = self._key(abstract)
        if callable(concrete) and not isinstance(concrete, type):
            factory: Factory = concrete  # type: ignore[assignment]
        else:
            instance = concrete

            def factory(container: Container, _instance=instance) -> Any:
                return _instance

        self._bindings[key] = factory
        self._singletons[key] = shared
        self._instances.pop(key, None)
        return self

    def singleton(self, abstract: str | type, concrete: Factory | Any) -> Container:
        """Bind as a shared (singleton) service."""
        return self.bind(abstract, concrete, shared=True)

    def instance(self, abstract: str | type, obj: Any) -> Container:
        """Register an existing object as a singleton instance."""
        key = self._key(abstract)
        self._instances[key] = obj
        self._singletons[key] = True
        self._bindings[key] = lambda c, _obj=obj: _obj
        return self

    def alias(self, abstract: str | type, alias: str | type) -> Container:
        """Create an alias pointing at an existing binding."""
        self._aliases[self._key(alias)] = self._key(abstract)
        return self

    def has(self, abstract: str | type) -> bool:
        """Return whether ``abstract`` can be resolved."""
        key = self._resolve_key(abstract)
        return key in self._bindings or key in self._instances

    def make(self, abstract: str | type) -> Any:
        """Resolve a service from the container."""
        key = self._resolve_key(abstract)
        if key in self._instances and self._singletons.get(key, False):
            return self._instances[key]
        if key not in self._bindings:
            raise BindingError(f"No binding for '{key}'")
        value = self._bindings[key](self)
        if self._singletons.get(key, False):
            self._instances[key] = value
        return value

    def get(self, abstract: str | type, default: Any = None) -> Any:
        """Resolve or return ``default`` when unbound."""
        try:
            return self.make(abstract)
        except BindingError:
            return default

    def _key(self, abstract: str | type) -> str:
        if isinstance(abstract, str):
            return abstract
        return f"{abstract.__module__}.{abstract.__qualname__}"

    def _resolve_key(self, abstract: str | type) -> str:
        key = self._key(abstract)
        seen: set[str] = set()
        while key in self._aliases and key not in seen:
            seen.add(key)
            key = self._aliases[key]
        return key
