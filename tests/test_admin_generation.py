from tpy.generator.admin_generator import AdminGenerator
from tpy.runtime.builder import Builder


def test_admin_generation_creates_react_app_from_schema(tmp_path):
    schema = """
database sqlite

model User {
  id: uuid primary
  name: string required
  email: string unique required
}

model Post {
  id: uuid primary
  title: string required
  body: string nullable
  user_id: uuid references User
}
"""
    (tmp_path / "schema.tpy").write_text(schema, encoding="utf-8")

    ast = Builder(tmp_path).parse_schema()
    AdminGenerator(tmp_path).generate(
        ast,
        api_base_url="http://127.0.0.1:8000",
    )

    admin = tmp_path / "admin"

    assert (admin / "package.json").exists()
    assert (admin / "vite.config.js").exists()
    assert (admin / "src" / "api" / "client.js").exists()
    assert (admin / "src" / "data" / "models.js").exists()
    assert (admin / "src" / "components" / "Layout.jsx").exists()
    assert (admin / "src" / "components" / "RecordForm.jsx").exists()
    assert (admin / "src" / "pages" / "ModelListPage.jsx").exists()
    assert (admin / "src" / "pages" / "ModelFormPage.jsx").exists()

    package = (admin / "package.json").read_text(encoding="utf-8")
    assert '"type": "module"' in package
    assert '"vite"' in package
    assert '"rollup": "npm:@rollup/wasm-node"' in package

    app = (admin / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "ModelListPage" in app
    assert "ModelFormPage" in app
    assert "models" in app

    models = (admin / "src" / "data" / "models.js").read_text(encoding="utf-8")
    assert '"routePrefix": "users"' in models
    assert '"routePrefix": "posts"' in models
    assert '"labelField": "name"' in models
    assert '"name": "user_id"' in models

    config = (admin / "src" / "config.js").read_text(encoding="utf-8")
    assert 'API_BASE_URL = "http://127.0.0.1:8000"' in config


def test_admin_generation_removes_legacy_per_model_pages(tmp_path):
    schema = """
database sqlite

model User {
  id: uuid primary
  name: string required
}
"""
    (tmp_path / "schema.tpy").write_text(schema, encoding="utf-8")
    legacy = tmp_path / "admin" / "src" / "pages"
    legacy.mkdir(parents=True)
    (legacy / "UserList.jsx").write_text("// legacy", encoding="utf-8")
    (legacy / "UserForm.jsx").write_text("// legacy", encoding="utf-8")

    ast = Builder(tmp_path).parse_schema()
    AdminGenerator(tmp_path).generate(ast)

    assert not (legacy / "UserList.jsx").exists()
    assert not (legacy / "UserForm.jsx").exists()
    assert (legacy / "ModelListPage.jsx").exists()
    assert (legacy / "ModelFormPage.jsx").exists()
