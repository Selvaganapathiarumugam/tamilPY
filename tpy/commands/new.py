from pathlib import Path

import typer

from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.console import Console
from tpy.utils.file_manager import FileManager


def register(app: typer.Typer):

    @app.command("new")
    def new(project_name: str):
        """
        Create a new TPY project.
        """

        root = Path(project_name)

        if FileManager.exists(root):
            Console.error(f"Project '{project_name}' already exists.")
            raise typer.Exit()

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

        templates = [
            "README.md",
            "main.py",
            "schema.tpy",
            "tpy.toml",
            ".env",
            ".gitignore",
            "requirements.txt",
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

        for template in templates:
            content = engine.render(
                f"project/{template}",
                context,
            )
            FileManager.write(
                root / template,
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
            root / "database" / "seeds" / "demo_seed.py",
            engine.render("project/database_seed_demo.py", context),
        )
        FileManager.write(
            root / "app" / "routes" / "__init__.py",
            "from fastapi import APIRouter\n\napi_router = APIRouter()\n",
        )

        Console.success(
            f"Project '{project_name}' created successfully."
        )
        Console.info("Next steps:")
        Console.info(f"  cd {project_name}")
        Console.info("  edit schema.tpy")
        Console.info("  tpy build")
