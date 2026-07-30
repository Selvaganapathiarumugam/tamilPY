from pathlib import Path

from tpy.parser.ast import ModelNode, ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.generated import write_generated


class ServiceGenerator:
    """
    Generate service classes from AST models.

    Writes one file per model under ``app/services/``.
    """

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

    def generate(self, ast: ProgramNode) -> None:
        """Generate service files for every model in the AST."""
        for model in ast.models:
            self.generate_service(model)

    def generate_service(self, model: ModelNode) -> None:
        """Build context, render template, and write one service file."""
        context = self.build_context(model)
        content = self.template.render(
            "generators/service.py.j2",
            context,
        )
        self.write_service(model.name, content)

    def build_context(self, model: ModelNode) -> dict:
        """Build Jinja context for a service class."""
        return {
            "class_name": model.name,
            "module_name": model.name.lower(),
        }

    def write_service(self, model_name: str, content: str) -> None:
        """Write the rendered service module."""
        filename = model_name.lower() + ".py"
        output = self.project_root / "app" / "services" / filename
        write_generated(output, content, force=self.force)
