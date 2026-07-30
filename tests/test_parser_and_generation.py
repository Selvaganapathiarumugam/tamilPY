import importlib.util

from tpy.database import Migration
from tpy.generator.migration_generator import MigrationGenerator
from tpy.generator.repository_generator import RepositoryGenerator
from tpy.parser.lexer import Lexer
from tpy.parser.parser import Parser
from tpy.providers.mongodb.provider import MongoProvider

SCHEMA = """
database postgres

model User {
  id: uuid primary index
  email: string unique required
  active: bool default true
}

model Post {
  id: uuid primary
  title: string required index
  body: string nullable
  user_id: uuid references User.id
  status: string default "draft"
}
"""


def parse_schema(source: str = SCHEMA):
    return Parser(Lexer(source).tokenize()).parse()


def test_parser_captures_defaults_constraints_and_references():
    ast = parse_schema()

    assert ast.database.provider == "postgres"
    assert [model.name for model in ast.models] == ["User", "Post"]

    user = ast.models[0]
    assert user.fields[0].name == "id"
    assert user.fields[0].constraints == ["primary", "index"]

    active = user.fields[2]
    assert active.has_default is True
    assert active.default is True

    post = ast.models[1]
    user_id = post.fields[3]
    assert user_id.reference.model == "User"
    assert user_id.reference.table == "user"
    assert user_id.reference.column == "id"

    status = post.fields[4]
    assert status.default == "draft"


def test_migration_generator_preserves_model_order_and_column_options(tmp_path):
    ast = parse_schema()

    MigrationGenerator(tmp_path).generate(ast)

    migrations = tmp_path / "database" / "migrations"
    assert (migrations / "001_user_migration.py").exists()
    assert (migrations / "002_post_migration.py").exists()

    user_migration = (migrations / "001_user_migration.py").read_text(
        encoding="utf-8"
    )
    assert 'self.create_table("user")' in user_migration
    assert ').primary()\n' in user_migration
    assert ".primary().index()" not in user_migration
    assert ".unique()" in user_migration
    assert ".default(True)" in user_migration

    post_migration = (migrations / "002_post_migration.py").read_text(
        encoding="utf-8"
    )
    assert ".nullable()" in post_migration
    assert ".references('user', 'id')" in post_migration
    assert ".default('draft')" in post_migration


def test_repository_generator_uses_schema_allowlist_before_sql(tmp_path):
    ast = parse_schema()

    RepositoryGenerator(tmp_path).generate(ast)

    repository = (
        tmp_path / "app" / "repositories" / "post.py"
    ).read_text(encoding="utf-8")

    assert (
        "COLUMNS = frozenset(('id', 'title', 'body', 'user_id', 'status'))"
        in repository
    )
    assert (
        "WRITABLE_COLUMNS = frozenset(('title', 'body', 'user_id', 'status'))"
        in repository
    )
    assert "payload = self._filter_payload(data, self.COLUMNS)" in repository
    assert "payload = self._filter_payload(data, self.WRITABLE_COLUMNS)" in repository
    assert "for key, value in data.items()" in repository
    assert "tuple(payload.values())" in repository
    assert "(*payload.values(), str(record_id))" in repository
    assert "def query(self):" in repository
    assert "QueryBuilder" in repository
    assert "return self.query().get()" in repository


def test_repository_generator_creates_mongo_repository_for_mongodb(tmp_path):
    ast = parse_schema(SCHEMA.replace("database postgres", "database mongodb"))

    RepositoryGenerator(tmp_path).generate(ast)

    repository_path = tmp_path / "app" / "repositories" / "post.py"
    repository = repository_path.read_text(encoding="utf-8")

    assert "Auto Generated MongoDB Repository" in repository
    assert "collection_insert_one" in repository
    assert "collection_update_one" in repository
    assert "SELECT *" not in repository

    spec = importlib.util.spec_from_file_location("post_repo", repository_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    db = FakeMongoProvider()
    repo = module.PostRepository(db)
    created = repo.create(
        {
            "id": "post-1",
            "title": "First",
            "body": "Draft",
            "user_id": "user-1",
            "ignored": "nope",
        }
    )
    assert created == {
        "id": "post-1",
        "title": "First",
        "body": "Draft",
        "user_id": "user-1",
    }

    updated = repo.update(
        "post-1",
        {
            "id": "post-2",
            "title": "Updated",
            "ignored": "still nope",
        },
    )
    assert updated["id"] == "post-1"
    assert updated["title"] == "Updated"
    assert "ignored" not in updated
    assert repo.delete("post-1") is True
    assert repo.find("post-1") is None


def test_mongo_provider_applies_migration_operations_as_collections_and_indexes():
    class UserMigration(Migration):
        def up(self):
            self.create_table("user")
            self.column("id", "uuid").primary()
            self.column("email", "string").unique()
            self.column("name", "string").index()
            self.column("team_id", "uuid").references("team", "id")

        def down(self):
            self.drop_table("user")

    db = FakeMongoDatabase()
    provider = MongoProvider(database_url="mongodb://127.0.0.1:27017/tpy")
    provider.connection = db

    migration = UserMigration()
    migration.up()
    provider.apply_operations(migration.operations)

    assert "user" in db.collections
    assert db["user"].indexes == [
        ("id", True),
        ("email", True),
        ("name", False),
        ("team_id", False),
    ]

    rollback = UserMigration()
    rollback.down()
    provider.apply_operations(rollback.operations)
    assert "user" not in db.collections


class FakeMongoProvider:
    def __init__(self):
        self.documents = {}

    def collection_all(self, collection):
        return list(self.documents.get(collection, []))

    def collection_find_one(self, collection, filters):
        for document in self.documents.get(collection, []):
            if all(document.get(key) == value for key, value in filters.items()):
                return dict(document)
        return None

    def collection_insert_one(self, collection, document):
        self.documents.setdefault(collection, []).append(dict(document))

    def collection_update_one(self, collection, filters, updates):
        document = self.collection_find_one(collection, filters)
        if document is None:
            return None
        for stored in self.documents[collection]:
            if all(stored.get(key) == value for key, value in filters.items()):
                stored.update(updates)
                return None
        return None

    def collection_delete_one(self, collection, filters):
        documents = self.documents.get(collection, [])
        before = len(documents)
        self.documents[collection] = [
            document
            for document in documents
            if not all(
                document.get(key) == value for key, value in filters.items()
            )
        ]
        return len(self.documents[collection]) < before


class FakeMongoCollection:
    def __init__(self):
        self.indexes = []

    def create_index(self, column, unique=False):
        self.indexes.append((column, unique))


class FakeMongoDatabase:
    def __init__(self):
        self.collections = {}

    def list_collection_names(self):
        return list(self.collections)

    def create_collection(self, name):
        self.collections[name] = FakeMongoCollection()

    def drop_collection(self, name):
        self.collections.pop(name, None)

    def __getitem__(self, name):
        if name not in self.collections:
            self.create_collection(name)
        return self.collections[name]
