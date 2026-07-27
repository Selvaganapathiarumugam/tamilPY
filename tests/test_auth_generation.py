from pathlib import Path

from tpy.generator.auth_generator import AuthGenerator
from tpy.runtime.builder import Builder


def test_auth_generation_adds_models_and_routes(tmp_path: Path):
    (tmp_path / "schema.tpy").write_text(
        "database sqlite\n\nmodel Post {\n  id: uuid primary\n  title: string required\n}\n",
        encoding="utf-8",
    )
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")

    count = AuthGenerator(tmp_path).generate()
    assert count >= 3

    schema = (tmp_path / "schema.tpy").read_text(encoding="utf-8")
    assert "model AuthRole" in schema
    assert "password: string required" in schema
    assert "role_id: uuid references AuthRole" in schema

    assert (tmp_path / "app" / "routes" / "auth.py").exists()
    assert (tmp_path / "app" / "security" / "jwt.py").exists()
    assert (tmp_path / "database" / "seeds" / "auth_role_seed.py").exists()
    assert (tmp_path / ".tpy_auth").exists()

    routes = (tmp_path / "app" / "routes" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "auth_router" in routes

    env = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "JWT_SECRET=" in env

    user_route = (tmp_path / "app" / "routes" / "user.py").read_text(
        encoding="utf-8"
    )
    assert "get_current_user" in user_route

    user_schema = (tmp_path / "app" / "schemas" / "user.py").read_text(
        encoding="utf-8"
    )
    assert "password" not in user_schema.split("class UserResponse")[-1]


def test_auth_merges_existing_user_model(tmp_path: Path):
    (tmp_path / "schema.tpy").write_text(
        """
database sqlite

model User {
  id: uuid primary
  name: string required
  email: string unique required
  age: int
}
""",
        encoding="utf-8",
    )
    AuthGenerator(tmp_path).generate()
    schema = (tmp_path / "schema.tpy").read_text(encoding="utf-8")
    assert schema.lower().count("model user") == 1
    assert "password: string required" in schema
    assert "age: int" in schema

    # AuthRole appears before User
    assert schema.index("AuthRole") < schema.index("model User")
