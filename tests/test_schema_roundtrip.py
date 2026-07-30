"""Round-trip and schema facade tests for serializer / JSON AST / validator."""

from __future__ import annotations

import pytest

from tpy.exceptions import TpyParseError
from tpy.parser.ast import ProgramNode
from tpy.parser.lexer import Lexer
from tpy.parser.parser import Parser
from tpy.parser.serializer import serialize_schema
from tpy.schema import (
    SchemaValidationError,
    from_json,
    parse_source,
    to_json,
    validate_program,
)
from tpy.schema.errors import SchemaDiagnostic


def _parse(source: str) -> ProgramNode:
    return Parser(Lexer(source).tokenize()).parse()


FIXTURES = [
    """\
database sqlite

model User {
  id: uuid primary
  email: string unique required
}
""",
    """\
database postgres

enum Status {
  draft
  published
}

model Post {
  id: uuid primary
  title: string required
  status: enum Status
  kind: enum(a, b)
  active: bool default true
}
""",
    """\
database mysql

model Student {
  id: uuid primary
}

model Course {
  id: uuid primary
}

model Enrollment {
  id: uuid primary
  student_id: uuid references Student on_delete cascade on_update restrict
  course_id: uuid references Course
  unique(student_id, course_id)
  relations {
    belongs_to Student as student via student_id
    belongs_to Course as course via course_id
  }
}
""",
    """\
database mongodb

model Tag {
  id: uuid primary
  name: string unique required
}

model Post {
  id: uuid primary
  title: string required
  relations {
    belongs_to_many Tag as tags through PostTag
  }
}

model PostTag {
  id: uuid primary
  post_id: uuid references Post
  tag_id: uuid references Tag
}
""",
]


@pytest.mark.parametrize("source", FIXTURES)
def test_parse_serialize_parse_roundtrip(source: str) -> None:
    first = _parse(source)
    text = serialize_schema(first)
    second = _parse(text)
    assert second == first
    assert serialize_schema(second) == text


@pytest.mark.parametrize("source", FIXTURES)
def test_json_ast_roundtrip(source: str) -> None:
    program = _parse(source)
    payload = to_json(program)
    assert "auth" not in payload or payload.get("auth") is None
    restored = from_json(payload)
    assert restored == program
    assert serialize_schema(restored) == serialize_schema(program)


def test_serializer_is_byte_stable_after_normalize() -> None:
    messy = """
database sqlite
model User {
id: uuid primary
email: string required unique
}
"""
    normalized = serialize_schema(_parse(messy))
    assert serialize_schema(_parse(normalized)) == normalized


def test_validate_undefined_reference_has_line_and_suggestion() -> None:
    program = _parse(
        """\
database sqlite

model Post {
  id: uuid primary
  user_id: uuid references Usr
}
"""
    )
    diagnostics = validate_program(program, filename="schema.tpy")
    errors = [d for d in diagnostics if d.severity == "error"]
    assert errors
    msg = errors[0].format()
    assert "schema.tpy:" in msg
    assert "Usr" in msg
    assert "undefined" in msg.lower() or "references" in msg.lower()


def test_validate_duplicate_field_names() -> None:
    program = _parse(
        """\
database sqlite

model Post {
  id: uuid primary
  status: string
  status: string
}
"""
    )
    errors = [d for d in validate_program(program) if d.severity == "error"]
    assert any("duplicate field" in d.message.lower() for d in errors)


def test_validate_duplicate_model_names() -> None:
    program = _parse(
        """\
database sqlite

model Post {
  id: uuid primary
}

model Post {
  id: uuid primary
}
"""
    )
    errors = [d for d in validate_program(program) if d.severity == "error"]
    assert any("duplicate model" in d.message.lower() for d in errors)


def test_validate_unique_together_unknown_column() -> None:
    program = _parse(
        """\
database sqlite

model Post {
  id: uuid primary
  unique(missing)
}
"""
    )
    errors = [d for d in validate_program(program) if d.severity == "error"]
    assert any("missing" in d.message for d in errors)


def test_validate_raises_on_build_path() -> None:
    program = _parse(
        """\
database sqlite

model Post {
  id: uuid primary
  user_id: uuid references Missing
}
"""
    )
    with pytest.raises(SchemaValidationError) as exc:
        validate_program(program, raise_on_error=True)
    assert "Missing" in str(exc.value)


def test_parse_source_helper() -> None:
    program = parse_source("database sqlite\n\nmodel A {\n  id: uuid primary\n}\n")
    assert program.database is not None
    assert program.database.provider == "sqlite"
    assert program.models[0].name == "A"


def test_diagnostic_format() -> None:
    d = SchemaDiagnostic(
        line=14,
        message="field 'user_id' references undefined model 'Usr'",
        severity="error",
        hint="did you mean 'User'?",
        filename="schema.tpy",
    )
    assert d.format() == (
        "schema.tpy:14 — field 'user_id' references undefined model 'Usr' "
        "(did you mean 'User'?)"
    )


def test_invalid_syntax_still_tpy_parse_error() -> None:
    with pytest.raises(TpyParseError):
        parse_source("model {")
