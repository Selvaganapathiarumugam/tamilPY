from pathlib import Path

from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.generated import write_generated


class ModelGenerator:

    TYPE_MAPPING = {
        "string": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "uuid": "UUID",
        "datetime": "datetime",
    }

    IMPORT_MAPPING = {
        "UUID": {
            "module": "uuid",
            "name": "UUID",
        },
        "datetime": {
            "module": "datetime",
            "name": "datetime",
        },
    }

    def __init__(
        self,
        project_root: Path | str = ".",
        *,
        force: bool = True,
    ):
        self.project_root = Path(project_root)
        self.force = force
        self.template = TemplateEngine()

    def generate(self, ast):
        for model in ast.models:
            self.generate_model(model)

    def generate_model(self, model):
        context = self.build_context(model)
        content = self.template.render(
            "generators/model.py.j2",
            context,
        )
        self.write_model(model.name, content)

    def build_context(self, model):
        imports = []
        fields = []

        for field in model.fields:
            python_type = self.map_type(field.datatype)
            fields.append({"name": field.name, "type": python_type})
            if python_type in self.IMPORT_MAPPING:
                imp = self.IMPORT_MAPPING[python_type]
                if imp not in imports:
                    imports.append(imp)

        return {
            "class_name": model.name,
            "imports": imports,
            "fields": fields,
        }

    def map_type(self, datatype):
        return self.TYPE_MAPPING.get(datatype, "str")

    def write_model(self, model_name, content):
        filename = model_name.lower() + ".py"
        output = self.project_root / "app" / "models" / filename
        write_generated(output, content, force=self.force)
