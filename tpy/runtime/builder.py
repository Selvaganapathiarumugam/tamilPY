from pathlib import Path

from tpy.generator.crud_generator import CrudGenerator
from tpy.parser.lexer import Lexer
from tpy.parser.parser import Parser


class Builder:
    """
    Orchestrate parsing ``schema.tpy`` and running code generators.
    """

    def __init__(self, project_root: Path | str = ".") -> None:
        """
        Args:
            project_root: Root directory of the target TPY project.
        """
        self.project_root = Path(project_root)
        self.generators = [
            CrudGenerator(self.project_root),
        ]

    @property
    def schema_path(self) -> Path:
        """Path to the project ``schema.tpy`` file."""
        return self.project_root / "schema.tpy"

    def build(self):
        """
        Parse the schema and run all generators.

        Returns:
            Parsed ``ProgramNode`` AST.

        Raises:
            FileNotFoundError: When ``schema.tpy`` is missing.
        """
        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"{self.schema_path} not found."
            )

        lexer = Lexer.from_file(self.schema_path)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        self.run_generators(ast)
        return ast

    def run_generators(self, ast) -> None:
        """Execute every registered generator."""
        for generator in self.generators:
            generator.generate(ast)
