from __future__ import annotations

import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Seeder(ABC):
    """
    Base class for database seed scripts.
    """

    def __init__(
        self,
        db: Any,
        project_root: Path | str | None = None,
    ) -> None:
        self.db = db
        if project_root is not None:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path(
                getattr(db, "project_root", Path("."))
            )

    @abstractmethod
    def run(self) -> None:
        """Insert seed data."""


class SeedRunner:
    """
    Discover and execute seed modules under ``database/seeds``.
    """

    def __init__(
        self,
        db: Any,
        project_root: Path | str = ".",
    ) -> None:
        self.db = db
        self.project_root = Path(project_root)

    @property
    def seeds_path(self) -> Path:
        """Directory containing seed modules."""
        return self.project_root / "database" / "seeds"

    def seed_files(self) -> list[Path]:
        """Return sorted Python seed files (skip ``__init__.py``)."""
        if not self.seeds_path.exists():
            return []
        return sorted(
            path
            for path in self.seeds_path.glob("*.py")
            if path.name != "__init__.py"
        )

    def run(self) -> list[str]:
        """
        Execute every seed module.

        Returns:
            Names of seed modules that ran.
        """
        ran: list[str] = []

        for path in self.seed_files():
            seeder = self.load_seeder(path)
            seeder.run()
            ran.append(path.stem)

        return ran

    def load_seeder(self, path: Path) -> Seeder:
        """Import a seed module and instantiate its ``Seeder`` subclass."""
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load seed: {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attribute in vars(module).values():
            if (
                isinstance(attribute, type)
                and issubclass(attribute, Seeder)
                and attribute is not Seeder
            ):
                return attribute(self.db, self.project_root)

        raise ImportError(f"No Seeder class found in {path}")
