from pathlib import Path

from tpy.parser.ast import FieldNode, ModelNode, ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.file_manager import FileManager
from tpy.utils.generated import is_pristine, write_generated
from tpy.exceptions import GeneratedFileConflict


class MigrationGenerator:
    """
    Generate migration classes from AST models.

    Writes one ordered file per model under ``database/migrations/``,
    for example ``001_user_migration.py``, ``002_post_migration.py``.
    """

    FLUENT_CONSTRAINTS = ("primary", "unique", "nullable", "index")

    def __init__(
        self,
        project_root: Path | str = ".",
        *,
        force: bool = True,
    ) -> None:
        """
        Args:
            project_root: Root directory of the target TPY project.
            force: Overwrite manually edited generated files.
        """
        self.project_root = Path(project_root)
        self.force = force
        self.template = TemplateEngine()
        self._enum_lookup: dict[str, list[str]] = {}

    def generate(self, ast: ProgramNode) -> None:
        """Generate ordered migration files for every model in the AST."""
        self._enum_lookup = {
            node.name: list(node.values) for node in ast.enums
        }
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
            columns.append(
                {
                    "name": field.name,
                    "datatype": self._sql_datatype(field),
                    "chain": self.build_chain(field),
                }
            )

        return {
            "table_name": model.name.lower(),
            "model_name": model.name,
            "columns": columns,
            "unique_together": model.unique_together,
        }

    def _sql_datatype(self, field: FieldNode) -> str:
        if field.datatype.startswith("enum"):
            return "enum"
        return field.datatype

    def _resolve_enum_values(self, field: FieldNode) -> list[str]:
        if field.enum_values:
            return list(field.enum_values)
        if field.datatype.startswith("enum:"):
            name = field.datatype.split(":", 1)[1]
            return list(self._enum_lookup.get(name, []))
        return []

    def build_chain(self, field: FieldNode) -> str:
        """
        Build the fluent ``Column`` method chain for a field.
        """
        chain = ""

        is_primary = "primary" in field.constraints

        for constraint in self.FLUENT_CONSTRAINTS:
            if constraint not in field.constraints:
                continue
            if constraint == "index" and is_primary:
                continue
            chain += f".{constraint}()"

        if field.reference is not None:
            kwargs = [
                f"{field.reference.table!r}",
                f"{field.reference.column!r}",
            ]
            if field.reference.on_delete:
                kwargs.append(f"on_delete={field.reference.on_delete!r}")
            if field.reference.on_update:
                kwargs.append(f"on_update={field.reference.on_update!r}")
            chain += f".references({', '.join(kwargs)})"

        enum_values = self._resolve_enum_values(field)
        if enum_values:
            # CHECK uses SQL identifiers without Python quotes in values list.
            sql_values = ", ".join(
                "'" + value.replace("'", "''") + "'" for value in enum_values
            )
            chain += f'.check("{field.name} IN ({sql_values})")'

        if field.has_default and field.default is not None:
            chain += f".default({field.default!r})"

        return chain

    def write_migration(
        self,
        model_name: str,
        content: str,
        sequence: int,
    ) -> None:
        """
        Write ``NNN_<model>_migration.py``, replacing older names for the model.
        """
        stem = model_name.lower()
        migrations_dir = (
            self.project_root / "database" / "migrations"
        )
        FileManager.create_directory(migrations_dir)

        legacy = migrations_dir / f"{stem}_migration.py"
        candidates = []
        if FileManager.exists(legacy):
            candidates.append(legacy)
        candidates.extend(migrations_dir.glob(f"*_{stem}_migration.py"))

        for path in candidates:
            if not self.force and not is_pristine(path):
                raise GeneratedFileConflict(str(path))

        for path in candidates:
            path.unlink()

        filename = f"{sequence:03d}_{stem}_migration.py"
        write_generated(
            migrations_dir / filename,
            content,
            force=self.force,
        )

    @property
    def migrations_path(self) -> Path:
        """Directory containing generated migration modules."""
        return self.project_root / "database" / "migrations"
