from pathlib import Path

from tpy.parser.ast import FieldNode, ModelNode, ProgramNode
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.file_manager import FileManager


class SchemaGenerator:
    """
    Generate Pydantic request/response schemas from AST models.

    Writes one file per model under ``app/schemas/``.
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
        Initialize the schema generator.

        Args:
            project_root: Root directory of the target TPY project.
        """
        self.project_root = Path(project_root)
        self.template = TemplateEngine()

    def generate(self, ast: ProgramNode) -> None:
        """
        Generate schema files for every model in the AST.

        Args:
            ast: Parsed program AST.
        """
        for model in ast.models:
            self.generate_schema(model)

    def generate_schema(self, model: ModelNode) -> None:
        """
        Build context, render the schema template, and write the file.

        Args:
            model: Model AST node to generate schemas for.
        """
        context = self.build_context(model)

        content = self.template.render(
            "generators/schema.py.j2",
            context,
        )

        self.write_schema(model.name, content)

    def build_context(self, model: ModelNode) -> dict:
        """
        Build Jinja template context for Create, Update, and Response schemas.

        Args:
            model: Model AST node.

        Returns:
            Template context with class names, imports, and field lists.
        """
        imports: list[dict[str, str]] = []
        create_fields: list[dict] = []
        update_fields: list[dict] = []
        response_fields: list[dict] = []

        for field in model.fields:
            python_type = self.map_type(field.datatype)
            self.collect_import(python_type, imports)

            field_info = self.build_field_info(field, python_type)

            if not self.is_primary(field):
                create_fields.append(field_info)
                update_fields.append(
                    {
                        **field_info,
                        "optional": True,
                    }
                )

            response_fields.append(field_info)

        return {
            "class_name": model.name,
            "imports": imports,
            "create_fields": create_fields,
            "update_fields": update_fields,
            "response_fields": response_fields,
        }

    def build_field_info(
        self,
        field: FieldNode,
        python_type: str,
    ) -> dict:
        """
        Build a single field descriptor for the template.

        Args:
            field: Field AST node.
            python_type: Mapped Python type name.

        Returns:
            Field descriptor with name, type, and optional flag.
        """
        return {
            "name": field.name,
            "type": python_type,
            "optional": self.is_optional(field),
        }

    def collect_import(
        self,
        python_type: str,
        imports: list[dict[str, str]],
    ) -> None:
        """
        Append a required import for the given Python type if needed.

        Args:
            python_type: Mapped Python type name.
            imports: Mutable list of import descriptors.
        """
        if python_type not in self.IMPORT_MAPPING:
            return

        import_info = self.IMPORT_MAPPING[python_type]

        if import_info not in imports:
            imports.append(import_info)

    def map_type(self, datatype: str) -> str:
        """
        Map a TPY datatype token to a Python type name.

        Args:
            datatype: TPY field datatype string.

        Returns:
            Python type name. Defaults to ``str`` when unknown.
        """
        return self.TYPE_MAPPING.get(datatype, "str")

    def is_primary(self, field: FieldNode) -> bool:
        """
        Return whether the field is marked as primary.

        Args:
            field: Field AST node.

        Returns:
            True if the field has the ``primary`` constraint.
        """
        return "primary" in field.constraints

    def is_optional(self, field: FieldNode) -> bool:
        """
        Return whether the field should be optional in Create schemas.

        Primary fields are handled separately. A field is optional when
        it is ``nullable`` or lacks ``required`` / ``primary``.

        Args:
            field: Field AST node.

        Returns:
            True when the Create schema field should allow ``None``.
        """
        if "nullable" in field.constraints:
            return True

        if "required" in field.constraints:
            return False

        if "primary" in field.constraints:
            return False

        return True

    def write_schema(
        self,
        model_name: str,
        content: str,
    ) -> None:
        """
        Write the rendered schema module to ``app/schemas/``.

        Args:
            model_name: Model class name used for the filename.
            content: Rendered Python source.
        """
        filename = model_name.lower() + ".py"

        output = (
            self.project_root
            / "app"
            / "schemas"
            / filename
        )

        FileManager.write(output, content)
