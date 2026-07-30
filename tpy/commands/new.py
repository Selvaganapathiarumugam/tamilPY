from pathlib import Path

import typer

from tpy.runtime.template_engine import TemplateEngine
from tpy.starter_templates import apply_template_files, get_template
from tpy.utils.console import Console
from tpy.utils.file_manager import FileManager


def register(app: typer.Typer):

    @app.command("new")
    def new(
        project_name: str,
        template: str | None = typer.Option(
            None,
            "--template",
            "-t",
            help="Starter template name (crm, institute-admin, …).",
        ),
    ):
        """
        Create a new TPY project.
        """

        root = Path(project_name)

        if FileManager.exists(root):
            Console.error(f"Project '{project_name}' already exists.")
            raise typer.Exit()

        if template is not None:
            try:
                get_template(template)
            except KeyError as error:
                Console.error(str(error))
                raise typer.Exit(1) from error

        engine = TemplateEngine()

        folders = [
            "app",
            "app/controllers",
            "app/models",
            "app/repositories",
            "app/routes",
            "app/schemas",
            "app/services",
            "app/providers",
            "app/middleware",
            "config",
            "database",
            "database/migrations",
            "database/seeds",
            "tests",
            "storage",
            "storage/logs",
            "storage/app",
            "storage/framework",
            "storage/framework/cache",
        ]

        packages = [
            "app",
            "app/controllers",
            "app/models",
            "app/repositories",
            "app/routes",
            "app/schemas",
            "app/services",
            "app/providers",
            "app/middleware",
            "config",
            "database",
            "database/seeds",
            "tests",
        ]

        # Template filename → project filename.
        # Dotfiles use non-hidden template names so setuptools
        # includes them in PyPI wheels.
        templates = [
            ("README.md", "README.md"),
            ("main.py", "app/main.py"),
            ("run_main.py", "main.py"),
            ("schema.tpy", "schema.tpy"),
            ("tpy.toml", "tpy.toml"),
            ("env", ".env"),
            ("gitignore", ".gitignore"),
            ("requirements.txt", "requirements.txt"),
        ]

        Console.info(f"Creating project '{project_name}'...")

        for folder in folders:
            FileManager.create_directory(root / folder)

        for package in packages:
            FileManager.write(
                root / package / "__init__.py",
                "",
            )

        context = {
            "PROJECT_NAME": project_name,
            "VERSION": "0.1.0",
        }

        for template_name, output_name in templates:
            content = engine.render(
                f"project/{template_name}",
                context,
            )
            FileManager.write(
                root / output_name,
                content,
            )

        FileManager.write(
            root / "app" / "providers" / "database.py",
            engine.render("project/app_providers_database.py", context),
        )
        FileManager.write(
            root / "app" / "logger.py",
            engine.render("project/app_logger.py", context),
        )
        FileManager.write(
            root / "app" / "schedule.py",
            engine.render("project/app_schedule.py", context),
        )
        FileManager.write(
            root / "database" / "seeds" / "demo_seed.py",
            engine.render("project/database_seed_demo.py", context),
        )
        FileManager.write(
            root / "app" / "routes" / "__init__.py",
            "from fastapi import APIRouter\n\napi_router = APIRouter()\n",
        )

        if template is not None:
            info = apply_template_files(root, template)
            Console.success(
                f"Applied template '{info.name}' "
                f"({len(info.models)} model(s))."
            )

        Console.success(
            f"Project '{project_name}' created successfully."
        )
        Console.info("Next steps:")
        Console.info(f"  cd {project_name}")
        if template is None:
            Console.info("  edit schema.tpy")
        Console.info("  tpy build")
