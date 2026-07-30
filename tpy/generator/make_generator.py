"""
Incremental ``make:*`` generation for a single model layer set.
"""

from __future__ import annotations

from pathlib import Path

from tpy.generator.controller_generator import ControllerGenerator
from tpy.generator.crud_generator import CrudGenerator
from tpy.generator.migration_generator import MigrationGenerator
from tpy.generator.model_generator import ModelGenerator
from tpy.generator.repository_generator import RepositoryGenerator
from tpy.generator.route_generator import RouteGenerator
from tpy.generator.schema_generator import SchemaGenerator
from tpy.generator.service_generator import ServiceGenerator
from tpy.parser.ast import FieldNode, ModelNode, ProgramNode
from tpy.schema import parse_file, parse_source, serialize, validate_program
from tpy.utils.file_manager import FileManager


def split_field_specs(fields: str) -> list[str]:
    """Split a ``--fields`` string on commas outside parentheses."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in fields:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            piece = "".join(current).strip()
            if piece:
                parts.append(piece)
            current = []
            continue
        current.append(char)
    piece = "".join(current).strip()
    if piece:
        parts.append(piece)
    return parts


def parse_field_specs(fields: str) -> list[FieldNode]:
    """
    Parse ``--fields`` specs into ``FieldNode`` list via the real schema parser.
    """
    specs = split_field_specs(fields)
    if not specs:
        return []
    body = "\n".join(f"  {spec}" for spec in specs)
    source = f"model __MakeTemp {{\n{body}\n}}\n"
    return list(parse_source(source).models[0].fields)


def ensure_primary(fields: list[FieldNode]) -> list[FieldNode]:
    """Prepend ``id: uuid primary`` when no primary field is present."""
    if any("primary" in field.constraints for field in fields):
        return fields
    return [
        FieldNode(name="id", datatype="uuid", constraints=["primary"]),
        *fields,
    ]


class MakeGenerator:
    """Append models to ``schema.tpy`` and regenerate one model at a time."""

    def __init__(
        self,
        project_root: Path | str = ".",
        *,
        force: bool = False,
    ) -> None:
        self.project_root = Path(project_root)
        self.force = force
        self.schema_path = self.project_root / "schema.tpy"

    def make_model(self, name: str, fields: str | None = None) -> ModelNode:
        """
        Append ``name`` to ``schema.tpy`` and generate CRUD files for it only.
        """
        if not self.schema_path.exists():
            raise FileNotFoundError(f"{self.schema_path} not found.")

        program = parse_file(self.schema_path)
        if any(model.name == name for model in program.models):
            raise ValueError(f"model '{name}' already exists in schema.tpy")

        field_nodes = ensure_primary(parse_field_specs(fields or ""))
        model = ModelNode(name=name, fields=field_nodes)
        program.models.append(model)
        validate_program(
            program,
            filename=self.schema_path.name,
            raise_on_error=True,
        )
        FileManager.write(self.schema_path, serialize(program))

        CrudGenerator(self.project_root).ensure_project_helpers()
        self._generate_model_stack(program, model)
        return model

    def make_service(self, name: str) -> ModelNode:
        """Regenerate only the service layer for an existing model."""
        program, model = self._require_model(name)
        ServiceGenerator(self.project_root, force=self.force).generate_service(
            model
        )
        return model

    def make_controller(self, name: str) -> ModelNode:
        """Regenerate only the controller layer for an existing model."""
        program, model = self._require_model(name)
        ControllerGenerator(
            self.project_root,
            force=self.force,
        ).generate_controller(model)
        return model

    def _require_model(self, name: str) -> tuple[ProgramNode, ModelNode]:
        if not self.schema_path.exists():
            raise FileNotFoundError(f"{self.schema_path} not found.")
        program = parse_file(self.schema_path)
        validate_program(
            program,
            filename=self.schema_path.name,
            raise_on_error=True,
        )
        for model in program.models:
            if model.name == name:
                return program, model
        raise ValueError(f"model '{name}' not found in schema.tpy")

    def _generate_model_stack(
        self,
        program: ProgramNode,
        model: ModelNode,
    ) -> None:
        force = self.force
        ModelGenerator(self.project_root, force=force).generate_model(model)

        sequence = next(
            (
                index
                for index, item in enumerate(program.models, start=1)
                if item.name == model.name
            ),
            len(program.models),
        )
        migrations = MigrationGenerator(self.project_root, force=force)
        migrations._enum_lookup = {
            node.name: list(node.values) for node in program.enums
        }
        migrations.generate_migration(model, sequence)

        SchemaGenerator(self.project_root, force=force).generate_schema(model)

        repositories = RepositoryGenerator(self.project_root, force=force)
        repositories.provider = (
            program.database.provider if program.database else ""
        )
        repositories.generate_repository(model)

        ServiceGenerator(self.project_root, force=force).generate_service(model)
        ControllerGenerator(
            self.project_root,
            force=force,
        ).generate_controller(model)

        auth_enabled = (self.project_root / ".tpy_auth").exists()
        routes = RouteGenerator(self.project_root, force=force)
        routes.generate_route(model, auth_enabled=auth_enabled)
        routes.write_router_index(program, auth_enabled=auth_enabled)
