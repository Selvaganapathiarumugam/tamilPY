from __future__ import annotations

import json
from pathlib import Path

from tpy.parser.ast import FieldNode, ModelNode, ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.starter_templates import load_theme
from tpy.utils.file_manager import FileManager


class AdminGenerator:
    """
    Generate a Vite + React admin dashboard from the parsed schema AST.

    Layout::

        admin/
          package.json
          vite.config.js
          index.html
          src/
            main.jsx
            App.jsx
            config.js
            styles.css
            api/client.js
            data/models.js
            utils/fields.js
            components/
              Layout.jsx
              PageHeader.jsx
              StatusMessage.jsx
              DataTable.jsx
              RecordForm.jsx
            pages/
              ModelListPage.jsx
              ModelFormPage.jsx
    """

    LABEL_FIELD_NAMES = ("name", "title", "email")

    SCAFFOLD_FILES = {
        "package.json": "admin/package.json.j2",
        "vite.config.js": "admin/vite.config.js.j2",
        "index.html": "admin/index.html.j2",
        "README.md": "admin/README.md.j2",
        "src/main.jsx": "admin/src/main.jsx.j2",
        "src/App.jsx": "admin/src/App.jsx.j2",
        "src/config.js": "admin/src/config.js.j2",
        "src/styles.css": "admin/src/styles.css.j2",
        "src/api/client.js": "admin/src/api/client.js.j2",
        "src/auth/session.js": "admin/src/auth/session.js.j2",
        "src/utils/fields.js": "admin/src/utils/fields.js.j2",
        "src/components/Layout.jsx": "admin/src/components/Layout.jsx.j2",
        "src/components/RequireAuth.jsx": "admin/src/components/RequireAuth.jsx.j2",
        "src/components/PageHeader.jsx": "admin/src/components/PageHeader.jsx.j2",
        "src/components/StatusMessage.jsx": "admin/src/components/StatusMessage.jsx.j2",
        "src/components/DataTable.jsx": "admin/src/components/DataTable.jsx.j2",
        "src/components/RecordForm.jsx": "admin/src/components/RecordForm.jsx.j2",
        "src/pages/LoginPage.jsx": "admin/src/pages/LoginPage.jsx.j2",
        "src/pages/ModelListPage.jsx": "admin/src/pages/ModelListPage.jsx.j2",
        "src/pages/ModelFormPage.jsx": "admin/src/pages/ModelFormPage.jsx.j2",
    }

    def __init__(self, project_root: Path | str = ".") -> None:
        self.project_root = Path(project_root)
        self.template = TemplateEngine()

    def generate(
        self,
        ast: ProgramNode,
        api_base_url: str = "http://127.0.0.1:8000",
        *,
        theme_name: str | None = None,
    ) -> None:
        """
        Generate admin app files for every model in the AST.
        """
        self.cleanup_legacy_pages()
        context = self.build_context(ast, api_base_url, theme_name=theme_name)
        self.write_scaffold(context)
        self.write_models_registry(ast)

    def build_context(
        self,
        ast: ProgramNode,
        api_base_url: str,
        *,
        theme_name: str | None = None,
    ) -> dict:
        """Build app-level template context."""
        models = [
            {
                "name": model.name,
                "route_prefix": self.route_prefix(model),
            }
            for model in ast.models
        ]
        theme = load_theme(theme_name, project_root=self.project_root)
        landing = theme.get("landing_model")
        landing_prefix = None
        if landing:
            for model in ast.models:
                if model.name == landing:
                    landing_prefix = self.route_prefix(model)
                    break
        if landing_prefix is None and models:
            landing_prefix = models[0]["route_prefix"]

        return {
            "api_base_url": api_base_url.rstrip("/"),
            "models": models,
            "has_models": bool(models),
            "theme_title": theme.get("title") or "Admin",
            "theme_subtitle": theme.get("subtitle") or "tamilPY dashboard",
            "theme_accent": theme.get("accent") or "#2563eb",
            "landing_route_prefix": landing_prefix or "",
        }

    def build_model_descriptor(
        self,
        model: ModelNode,
        ast: ProgramNode,
    ) -> dict:
        """Build one model entry for the generated models registry."""
        primary = self.find_primary(model)
        return {
            "name": model.name,
            "routePrefix": self.route_prefix(model),
            "primaryName": primary.name if primary else "id",
            "fields": [
                self.field_info(field, ast)
                for field in model.fields
            ],
        }

    def field_info(
        self,
        field: FieldNode,
        ast: ProgramNode,
    ) -> dict:
        """Build a serializable field descriptor for React templates."""
        reference = None
        if field.reference:
            reference_model = self.find_model(ast, field.reference.model)
            reference_primary = (
                self.find_primary(reference_model)
                if reference_model
                else None
            )
            reference = {
                "model": field.reference.model,
                "routePrefix": self.route_prefix(reference_model)
                if reference_model
                else field.reference.model.lower() + "s",
                "valueField": reference_primary.name
                if reference_primary
                else field.reference.column,
                "labelField": self.label_field(reference_model)
                if reference_model
                else field.reference.column,
            }

        return {
            "name": field.name,
            "type": field.datatype,
            "required": "required" in field.constraints,
            "primary": "primary" in field.constraints,
            "nullable": "nullable" in field.constraints,
            "hasDefault": field.has_default,
            "defaultValue": field.default,
            "reference": reference,
        }

    def write_scaffold(self, context: dict) -> None:
        """Write app-level files shared by every generated admin page."""
        for output, template in self.SCAFFOLD_FILES.items():
            FileManager.write(
                self.project_root / "admin" / output,
                self.template.render(template, context),
            )

    def write_models_registry(self, ast: ProgramNode) -> None:
        """Write ``src/data/models.js`` — the only model-specific generated data."""
        descriptors = [
            self.build_model_descriptor(model, ast)
            for model in ast.models
        ]
        payload = json.dumps(descriptors, indent=2)
        content = (
            "/** Auto-generated from schema.tpy — do not edit by hand. */\n"
            f"export const models = {payload};\n\n"
            "export function getModel(routePrefix) {\n"
            "  return models.find(\n"
            "    (model) => model.routePrefix === routePrefix\n"
            "  ) || null;\n"
            "}\n"
        )
        FileManager.write(
            self.project_root / "admin" / "src" / "data" / "models.js",
            content,
        )

    def cleanup_legacy_pages(self) -> None:
        """
        Remove old per-model page files from earlier admin generators.

        Keeps ``ModelListPage.jsx`` / ``ModelFormPage.jsx``.
        """
        pages_dir = self.project_root / "admin" / "src" / "pages"
        if not pages_dir.exists():
            return

        keep = {"ModelListPage.jsx", "ModelFormPage.jsx"}
        for path in pages_dir.glob("*.jsx"):
            if path.name not in keep:
                path.unlink(missing_ok=True)

    def route_prefix(self, model: ModelNode) -> str:
        """Return the backend route prefix for a model."""
        return model.name.lower() + "s"

    def find_primary(self, model: ModelNode) -> FieldNode | None:
        """Return the first primary field for a model."""
        for field in model.fields:
            if "primary" in field.constraints:
                return field
        return None

    def find_model(
        self,
        ast: ProgramNode,
        name: str,
    ) -> ModelNode | None:
        """Find a model by name."""
        for model in ast.models:
            if model.name == name:
                return model
        return None

    def label_field(self, model: ModelNode | None) -> str:
        """Choose a human-readable label field for foreign-key selects."""
        if model is None:
            return "id"

        field_names = {field.name for field in model.fields}
        for candidate in self.LABEL_FIELD_NAMES:
            if candidate in field_names:
                return candidate

        primary = self.find_primary(model)
        return primary.name if primary else "id"
