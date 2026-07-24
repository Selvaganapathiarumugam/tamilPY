from pathlib import Path

from tpy.parser.ast import FieldNode, ModelNode, ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.file_manager import FileManager


class MigrationGenerator:
    """
    Generate migration classes from AST models.

    Writes one file per model under ``database/migrations/``.
    """

    FLUENT_CONSTRAINTS = {"primary", "unique", "nullable", "index"}

    def __init__(self, project_root: Path | str = ".") -> None:
        """
        Args:
            project_root: Root directory of the target TPY project.
        """
        self.project_root = Path(project_root)
        self.template = TemplateEngine()

    def generate(self, ast: ProgramNode) -> None:
        """Generate migration files for every model in the AST."""
        for model in ast.models:
            self.generate_migration(model)

    def generate_migration(self, model: ModelNode) -> None:
        """Build context, render template, and write one migration file."""
        context = self.build_context(model)
        content = self.template.render(
            "generators/migration.py.j2",
            context,
        )
        self.write_migration(model.name, content)

    def build_context(self, model: ModelNode) -> dict:
        """
        Build Jinja context for a migration class.

        Args:
            model: Model AST node.

        Returns:
            Template context with table metadata and columns.
        """
        columns = []

        for field in model.fields:
            constraints = self.map_constraints(field)
            chain = "".join(
                f".{constraint}()"
                for constraint in constraints
            )
            columns.append(
                {
                    "name": field.name,
                    "datatype": field.datatype,
                    "chain": chain,
                }
            )

        return {
            "table_name": model.name.lower(),
            "model_name": model.name,
            "columns": columns,
        }

    def map_constraints(self, field: FieldNode) -> list[str]:
        """
        Map AST constraints to Migration fluent method names.

        Args:
            field: Field AST node.

        Returns:
            Constraint method names supported by ``Column``.
        """
        return [
            constraint
            for constraint in field.constraints
            if constraint in self.FLUENT_CONSTRAINTS
        ]

    def write_migration(self, model_name: str, content: str) -> None:
        """Write the rendered migration module."""
        filename = model_name.lower() + "_migration.py"
        output = (
            self.project_root
            / "database"
            / "migrations"
            / filename
        )
        FileManager.write(output, content)
