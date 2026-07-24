from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class TemplateEngine:
    """
    Renders Jinja2 templates.
    """

    def __init__(self):
        template_path = (
            Path(__file__).resolve().parent.parent / "templates"
        )

        self.env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template: str, context: dict | None = None) -> str:
        context = context or {}
        return self.env.get_template(template).render(**context)