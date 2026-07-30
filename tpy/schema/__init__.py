"""
Shared schema facade: parse, serialize, JSON AST, validate.

Studio, ``make:*``, and templates should use this module rather than
calling the lexer/parser directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tpy.parser.ast import ProgramNode
from tpy.parser.json_ast import from_json as _from_json
from tpy.parser.json_ast import to_json as _to_json
from tpy.parser.lexer import Lexer
from tpy.parser.parser import Parser
from tpy.parser.serializer import serialize_schema
from tpy.schema.errors import SchemaDiagnostic, SchemaValidationError
from tpy.schema.validator import validate_program


def parse_source(source: str) -> ProgramNode:
    """Parse ``schema.tpy`` source text into a ``ProgramNode``."""
    return Parser(Lexer(source).tokenize()).parse()


def parse_file(path: Path | str) -> ProgramNode:
    """Parse a ``schema.tpy`` file from disk."""
    file_path = Path(path)
    return parse_source(file_path.read_text(encoding="utf-8"))


def serialize(program: ProgramNode) -> str:
    """Serialize ``program`` to deterministic ``schema.tpy`` text."""
    return serialize_schema(program)


def to_json(program: ProgramNode) -> dict[str, Any]:
    """Convert ``program`` to Studio JSON AST (without auth)."""
    return _to_json(program)


def from_json(payload: dict[str, Any]) -> ProgramNode:
    """Build ``ProgramNode`` from Studio JSON AST."""
    return _from_json(payload)


__all__ = [
    "SchemaDiagnostic",
    "SchemaValidationError",
    "from_json",
    "parse_file",
    "parse_source",
    "serialize",
    "serialize_schema",
    "to_json",
    "validate_program",
]
