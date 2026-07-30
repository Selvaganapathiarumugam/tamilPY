from pathlib import Path

from tpy.config.loader import ConfigLoader
from tpy.generator.controller_generator import ControllerGenerator
from tpy.generator.migration_generator import MigrationGenerator
from tpy.generator.model_generator import ModelGenerator
from tpy.generator.repository_generator import RepositoryGenerator
from tpy.generator.route_generator import RouteGenerator
from tpy.generator.schema_generator import SchemaGenerator
from tpy.generator.service_generator import ServiceGenerator
from tpy.parser.ast import ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.file_manager import FileManager


class CrudGenerator:
    """
    Orchestrate full CRUD code generation for every AST model.

    Runs model, migration, schema, repository, service, controller,
    and route generators in order.
    """

    def __init__(self, project_root: Path | str = ".") -> None:
        """
        Args:
            project_root: Root directory of the target TPY project.
        """
        self.project_root = Path(project_root)
        self.template = TemplateEngine()
        self.generators = [
            ModelGenerator(self.project_root, force=True),
            MigrationGenerator(self.project_root, force=True),
            SchemaGenerator(self.project_root, force=True),
            RepositoryGenerator(self.project_root, force=True),
            ServiceGenerator(self.project_root, force=True),
            ControllerGenerator(self.project_root, force=True),
            RouteGenerator(self.project_root, force=True),
        ]

    def generate(self, ast: ProgramNode) -> None:
        """
        Run every registered generator against the AST.

        Args:
            ast: Parsed program AST.
        """
        self.ensure_project_helpers()

        for generator in self.generators:
            generator.generate(ast)

    def ensure_project_helpers(self) -> None:
        """Create app entrypoint, provider, logger, and seeds when missing."""
        project_name = self._project_name()

        self._ensure_file(
            self.project_root / "app" / "main.py",
            "project/main.py",
            {"PROJECT_NAME": project_name},
        )
        self._ensure_file(
            self.project_root / "main.py",
            "project/run_main.py",
        )
        self._ensure_file(
            self.project_root / "app" / "providers" / "database.py",
            "project/app_providers_database.py",
        )
        self._ensure_file(
            self.project_root / "app" / "logger.py",
            "project/app_logger.py",
        )

        seeds_dir = self.project_root / "database" / "seeds"
        FileManager.create_directory(seeds_dir)

        init_path = seeds_dir / "__init__.py"
        if not FileManager.exists(init_path):
            FileManager.write(init_path, "")

        demo_seed = seeds_dir / "demo_seed.py"
        if not FileManager.exists(demo_seed):
            content = self.template.render(
                "project/database_seed_demo.py",
                {},
            )
            FileManager.write(demo_seed, content)

        FileManager.create_directory(
            self.project_root / "storage" / "logs"
        )
    def _project_name(self) -> str:
        """Resolve project display name for templates."""
        try:
            settings = ConfigLoader(self.project_root).load()
            if settings.name:
                return settings.name
        except Exception:
            pass
        return self.project_root.resolve().name

    def _ensure_file(
        self,
        output: Path,
        template_name: str,
        context: dict | None = None,
    ) -> None:
        if FileManager.exists(output):
            return
        content = self.template.render(template_name, context or {})
        FileManager.write(output, content)
