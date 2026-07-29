"""SQLite integration tests for QueryBuilder."""

from pathlib import Path

import pytest

from tpy.providers.sqlite.provider import SQLiteProvider
from tpy.query import (
    GrammarError,
    InvalidColumnError,
    QueryBuilder,
    Raw,
)


@pytest.fixture()
def db(tmp_path: Path):
    path = tmp_path / "qb.sqlite3"
    provider = SQLiteProvider(database_url=f"sqlite:///{path}")
    provider.connect()
    provider.execute(
        """
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            status TEXT NOT NULL,
            age INTEGER
        )
        """
    )
    provider.execute(
        "INSERT INTO users (id, email, status, age) VALUES (?, ?, ?, ?)",
        ("1", "a@x.com", "active", 20),
    )
    provider.execute(
        "INSERT INTO users (id, email, status, age) VALUES (?, ?, ?, ?)",
        ("2", "b@x.com", "inactive", 30),
    )
    provider.execute(
        "INSERT INTO users (id, email, status, age) VALUES (?, ?, ?, ?)",
        ("3", "c@x.com", "active", 40),
    )
    yield provider
    provider.close()


def test_where_get_and_count(db):
    cols = frozenset({"id", "email", "status", "age"})
    rows = (
        QueryBuilder(db, "users", cols)
        .where("status", "active")
        .order_by("age", "desc")
        .get()
    )
    assert [r["id"] for r in rows] == ["3", "1"]
    assert QueryBuilder(db, "users", cols).where("status", "active").count() == 2


def test_column_whitelist(db):
    cols = frozenset({"id", "email"})
    with pytest.raises(InvalidColumnError):
        QueryBuilder(db, "users", cols).where("status", "active")


def test_paginate(db):
    cols = frozenset({"id", "email", "status", "age"})
    page = (
        QueryBuilder(db, "users", cols)
        .order_by("id")
        .paginate(page=1, per_page=2)
    )
    assert page.total == 3
    assert len(page.items) == 2
    assert page.last_page == 2
    assert "meta" in page.to_dict()


def test_update_requires_where(db):
    cols = frozenset({"id", "email", "status", "age"})
    with pytest.raises(GrammarError):
        QueryBuilder(db, "users", cols).update({"status": "x"})


def test_update_and_delete(db):
    cols = frozenset({"id", "email", "status", "age"})
    QueryBuilder(db, "users", cols).where("id", "2").update(
        {"status": "active"}
    )
    row = QueryBuilder(db, "users", cols).find("2")
    assert row is not None
    assert row["status"] == "active"
    QueryBuilder(db, "users", cols).where("id", "2").delete()
    assert QueryBuilder(db, "users", cols).find("2") is None


def test_where_in_and_raw(db):
    cols = frozenset({"id", "email", "status", "age"})
    rows = (
        QueryBuilder(db, "users", cols)
        .where_in("id", ["1", "3"])
        .select("id", Raw("email"))
        .get()
    )
    assert {r["id"] for r in rows} == {"1", "3"}


def test_to_sql_uses_placeholder(db):
    cols = frozenset({"id", "email", "status", "age"})
    sql, params = (
        QueryBuilder(db, "users", cols)
        .where("email", "a@x.com")
        .to_sql()
    )
    assert "?" in sql
    assert params == ["a@x.com"]
