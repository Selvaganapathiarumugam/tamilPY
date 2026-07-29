"""Parser tests for schema.tpy relations blocks."""

from tpy.parser.lexer import Lexer
from tpy.parser.parser import Parser
from tpy.query import registry_from_program


def _parse(source: str):
    return Parser(Lexer(source).tokenize()).parse()


def test_parse_all_relation_kinds():
    ast = _parse(
        """
database sqlite

model User {
  id: uuid primary
  email: string
  relations {
    has_many Post as posts
    has_one Profile as profile
    belongs_to_many AuthRole as roles through UserRole
  }
}

model Post {
  id: uuid primary
  user_id: uuid references User
  title: string
  relations {
    belongs_to User as author via user_id
  }
}

model Profile {
  id: uuid primary
  user_id: uuid references User
}

model AuthRole {
  id: uuid primary
  name: string
}

model UserRole {
  id: uuid primary
  user_id: uuid references User
  authrole_id: uuid references AuthRole
  unique(user_id, authrole_id)
}
"""
    )
    user = next(m for m in ast.models if m.name == "User")
    assert len(user.relations) == 3
    kinds = {r.kind for r in user.relations}
    assert kinds == {"has_many", "has_one", "belongs_to_many"}
    posts = next(r for r in user.relations if r.name == "posts")
    assert posts.model == "Post"
    roles = next(r for r in user.relations if r.name == "roles")
    assert roles.through == "UserRole"

    post = next(m for m in ast.models if m.name == "Post")
    author = post.relations[0]
    assert author.kind == "belongs_to"
    assert author.foreign_key == "user_id"
    assert author.name == "author"


def test_schemas_without_relations_still_parse():
    ast = _parse(
        """
database sqlite
model User {
  id: uuid primary
}
"""
    )
    assert ast.models[0].relations == []


def test_registry_from_program_defaults():
    ast = _parse(
        """
database sqlite
model User {
  id: uuid primary
  relations {
    has_many Post as posts
  }
}
model Post {
  id: uuid primary
  user_id: uuid references User
  relations {
    belongs_to User as author via user_id
  }
}
"""
    )
    registry = registry_from_program(ast)
    posts = registry.get("User", "posts")
    assert posts.definition.foreign_key == "user_id"
    author = registry.get("Post", "author")
    assert author.definition.foreign_key == "user_id"
