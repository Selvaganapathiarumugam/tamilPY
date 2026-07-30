from tpy.database.migration import Migration
from tpy.providers.sqlite.provider import SQLiteProvider


class _SampleMigration(Migration):
    def up(self) -> None:
        self.create_table("demo")
        self.column("id", "uuid").primary()
        self.column("email", "string").unique()
        self.column("role", "enum").check("role IN ('a', 'b')")
        self.column("user_id", "uuid").references(
            "user",
            "id",
            on_delete="cascade",
            on_update="restrict",
        )
        self.unique("email", "user_id")

    def down(self) -> None:
        self.drop_table("demo")


def test_quote_identifier_escapes_double_quotes():
    provider = SQLiteProvider(database_url="sqlite:///:memory:")
    assert provider.quote_identifier("user") == '"user"'
    assert provider.quote_identifier('a"b') == '"a""b"'


def test_compile_operations_includes_fk_actions_unique_and_check():
    provider = SQLiteProvider(database_url="sqlite:///:memory:")
    migration = _SampleMigration()
    migration.up()
    sql = provider.compile_operations(migration.operations)
    create = sql[0]
    assert "CREATE TABLE IF NOT EXISTS" in create
    assert "REFERENCES" in create
    assert "ON DELETE CASCADE" in create
    assert "ON UPDATE RESTRICT" in create
    assert "UNIQUE" in create
    assert "CHECK" in create


def test_bind_parameters_passthrough_for_sqlite():
    provider = SQLiteProvider(database_url="sqlite:///:memory:")
    sql, params = provider.bind_parameters(
        "SELECT * FROM t WHERE id = ?",
        ("abc",),
    )
    assert sql == "SELECT * FROM t WHERE id = ?"
    assert params == ("abc",)


def test_provider_context_manager_closes():
    provider = SQLiteProvider(database_url="sqlite:///:memory:")
    with provider as db:
        assert db.connection is not None
    assert provider.connection is None
