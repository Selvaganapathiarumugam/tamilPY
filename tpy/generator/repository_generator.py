from pathlib import Path

from tpy.parser.ast import FieldNode, ModelNode, ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.file_manager import FileManager


class RepositoryGenerator:
    """
    Generate repository classes from AST models.

    Writes one file per model under ``app/repositories/``.
    """

    TYPE_MAPPING: dict[str, str] = {
        "string": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "uuid": "UUID",
        "datetime": "datetime",
    }

    def __init__(self, project_root: Path | str = ".") -> None:
        """
        Args:
            project_root: Root directory of the target TPY project.
        """
        self.project_root = Path(project_root)
        self.template = TemplateEngine()
        self.provider = ""

    def generate(self, ast: ProgramNode) -> None:
        """Generate repository files for every model in the AST."""
        self.provider = ast.database.provider if ast.database else ""
        for model in ast.models:
            self.generate_repository(model)

    def generate_repository(self, model: ModelNode) -> None:
        """Build context, render template, and write one repository file."""
        context = self.build_context(model)
        template_name = "generators/repository.py.j2"
        if context["provider"] in {"mongo", "mongodb"}:
            template_name = "generators/mongo_repository.py.j2"
        content = self.template.render(
            template_name,
            context,
        )
        self.write_repository(model.name, content)

    def build_context(self, model: ModelNode) -> dict:
        """
        Build Jinja context for a repository class.

        Args:
            model: Model AST node.

        Returns:
            Template context with table and primary-key metadata.
        """
        primary = self.find_primary(model)
        columns = tuple(field.name for field in model.fields)
        primary_key = primary.name if primary else "id"
        writable_columns = tuple(
            field.name
            for field in model.fields
            if field.name != primary_key
        )

        return {
            "class_name": model.name,
            "module_name": model.name.lower(),
            "table_name": model.name.lower(),
            "primary_key": primary_key,
            "primary_type": self.map_type(
                primary.datatype if primary else "int"
            ),
            "columns": repr(columns),
            "writable_columns": repr(writable_columns),
            "provider": self.provider,
        }

    def find_primary(self, model: ModelNode) -> FieldNode | None:
        """Return the first primary field, if any."""
        for field in model.fields:
            if "primary" in field.constraints:
                return field
        return None

    def map_type(self, datatype: str) -> str:
        """Map a TPY datatype to a Python type name."""
        return self.TYPE_MAPPING.get(datatype, "str")

    def write_repository(self, model_name: str, content: str) -> None:
        """Write the rendered repository module."""
        filename = model_name.lower() + ".py"
        output = (
            self.project_root
            / "app"
            / "repositories"
            / filename
        )
        FileManager.write(output, content)
