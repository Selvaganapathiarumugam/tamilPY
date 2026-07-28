from tpy.parser.lexer import Lexer
from tpy.parser.parser import Parser
from tpy.exceptions import TpyParseError


def _parse(source: str):
    return Parser(Lexer(source).tokenize()).parse()


def test_parse_enum_block_and_field_reference():
    ast = _parse(
        """
database sqlite

enum Status {
  draft
  published
}

model Post {
  id: uuid primary
  status: enum Status
  kind: enum(a, b)
}
"""
    )
    assert len(ast.enums) == 1
    assert ast.enums[0].name == "Status"
    assert ast.enums[0].values == ["draft", "published"]
    post = ast.models[0]
    assert post.fields[1].datatype == "enum:Status"
    assert post.fields[2].datatype == "enum"
    assert post.fields[2].enum_values == ["a", "b"]


def test_parse_composite_unique_and_fk_actions():
    ast = _parse(
        """
database sqlite

model Enrollment {
  id: uuid primary
  student_id: uuid references Student on_delete cascade on_update restrict
  course_id: uuid references Course
  unique(student_id, course_id)
}
"""
    )
    model = ast.models[0]
    assert model.unique_together == [["student_id", "course_id"]]
    fk = model.fields[1].reference
    assert fk is not None
    assert fk.on_delete == "cascade"
    assert fk.on_update == "restrict"


def test_parse_error_is_tpy_parse_error():
    try:
        _parse("model {")
        assert False, "expected TpyParseError"
    except TpyParseError:
        pass
