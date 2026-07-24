from pathlib import Path

from tpy.parser.ast import ModelNode, ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.file_manager import FileManager


class ControllerGenerator:
    """
    Generate controller classes from AST models.

    Writes one file per model under ``app/controllers/``.
    """

    def __init__(self, project_root: Path | str = ".") -> None:
        """
        Args:
            project_root: Root directory of the target TPY project.
        """
        self.project_root = Path(project_root)
        self.template = TemplateEngine()

    def generate(self, ast: ProgramNode) -> None:
        """Generate controller files for every model in the AST."""
        for model in ast.models:
            self.generate_controller(model)

    def generate_controller(self, model: ModelNode) -> None:
        """Build context, render template, and write one controller file."""
        context = self.build_context(model)
        content = self.template.render(
            "generators/controller.py.j2",
            context,
        )
        self.write_controller(model.name, content)

    def build_context(self, model: ModelNode) -> dict:
        """Build Jinja context for a controller class."""
        return {
            "class_name": model.name,
            "module_name": model.name.lower(),
        }

    def write_controller(self, model_name: str, content: str) -> None:
        """Write the rendered controller module."""
        filename = model_name.lower() + ".py"
        output = (
            self.project_root
            / "app"
            / "controllers"
            / filename
        )
        FileManager.write(output, content)
