from pathlib import Path

from tpy.parser.ast import FieldNode, ModelNode, ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.file_manager import FileManager


class MigrationGenerator:
    """
    Generate migration classes from AST models.

    Writes one ordered file per model under ``database/migrations/``,
    for example ``001_user_migration.py``, ``002_post_migration.py``.
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
        """Generate ordered migration files for every model in the AST."""
        for index, model in enumerate(ast.models, start=1):
            self.generate_migration(model, index)

    def generate_migration(self, model: ModelNode, sequence: int) -> None:
        """Build context, render template, and write one migration file."""
        context = self.build_context(model)
        content = self.template.render(
            "generators/migration.py.j2",
            context,
        )
        self.write_migration(model.name, content, sequence)

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

    def write_migration(
        self,
        model_name: str,
        content: str,
        sequence: int,
    ) -> None:
        """
        Write ``NNN_<model>_migration.py``, replacing older names for the model.

        Args:
            model_name: Model class name.
            content: Rendered migration source.
            sequence: 1-based order from ``schema.tpy``.
        """
        stem = model_name.lower()
        migrations_dir = (
            self.project_root / "database" / "migrations"
        )
        FileManager.create_directory(migrations_dir)

        # Remove legacy and previous numbered files for this model.
        legacy = migrations_dir / f"{stem}_migration.py"
        if FileManager.exists(legacy):
            legacy.unlink()

        for path in migrations_dir.glob(f"*_{stem}_migration.py"):
            path.unlink()

        filename = f"{sequence:03d}_{stem}_migration.py"
        FileManager.write(migrations_dir / filename, content)

    @property
    def migrations_path(self) -> Path:
        """Directory containing generated migration modules."""
        return self.project_root / "database" / "migrations"
