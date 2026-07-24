from pathlib import Path

from tpy.parser.ast import FieldNode, ModelNode, ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.file_manager import FileManager


class RouteGenerator:
    """
    Generate FastAPI route modules from AST models.

    Writes one file per model under ``app/routes/``.
    """

    TYPE_MAPPING: dict[str, str] = {
        "string": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "uuid": "UUID",
        "datetime": "datetime",
    }

    IMPORT_MAPPING: dict[str, dict[str, str]] = {
        "UUID": {
            "module": "uuid",
            "name": "UUID",
        },
        "datetime": {
            "module": "datetime",
            "name": "datetime",
        },
    }

    def __init__(self, project_root: Path | str = ".") -> None:
        """
        Args:
            project_root: Root directory of the target TPY project.
        """
        self.project_root = Path(project_root)
        self.template = TemplateEngine()

    def generate(self, ast: ProgramNode) -> None:
        """Generate route files for every model in the AST."""
        for model in ast.models:
            self.generate_route(model)

        self.write_router_index(ast)

    def generate_route(self, model: ModelNode) -> None:
        """Build context, render template, and write one route file."""
        context = self.build_context(model)
        content = self.template.render(
            "generators/route.py.j2",
            context,
        )
        self.write_route(model.name, content)

    def build_context(self, model: ModelNode) -> dict:
        """Build Jinja context for a route module."""
        primary = self.find_primary(model)
        primary_type = self.map_type(
            primary.datatype if primary else "int"
        )

        return {
            "class_name": model.name,
            "module_name": model.name.lower(),
            "route_prefix": model.name.lower() + "s",
            "primary_type": primary_type,
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

    def write_route(self, model_name: str, content: str) -> None:
        """Write the rendered route module."""
        filename = model_name.lower() + ".py"
        output = (
            self.project_root
            / "app"
            / "routes"
            / filename
        )
        FileManager.write(output, content)

    def write_router_index(self, ast: ProgramNode) -> None:
        """
        Write ``app/routes/__init__.py`` that aggregates model routers.

        Args:
            ast: Parsed program AST.
        """
        lines = [
            '"""Auto-generated route registry."""',
            "",
            "from fastapi import APIRouter",
            "",
        ]

        for model in ast.models:
            module = model.name.lower()
            lines.append(
                f"from app.routes.{module} import router as {module}_router"
            )

        lines.extend(["", "api_router = APIRouter()", ""])

        for model in ast.models:
            module = model.name.lower()
            lines.append(
                f"api_router.include_router({module}_router)"
            )

        lines.append("")

        FileManager.write(
            self.project_root / "app" / "routes" / "__init__.py",
            "\n".join(lines),
        )
