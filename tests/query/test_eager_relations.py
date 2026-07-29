"""Eager loading integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from tpy.providers.sqlite.provider import SQLiteProvider
from tpy.query import QueryBuilder, RelationDefinition, RelationRegistry


@pytest.fixture()
def db(tmp_path: Path):
    path = tmp_path / "rel.sqlite3"
    provider = SQLiteProvider(database_url=f"sqlite:///{path}")
    provider.connect()
    provider.execute(
        "CREATE TABLE users (id TEXT PRIMARY KEY, name TEXT)"
    )
    provider.execute(
        """
        CREATE TABLE posts (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT
        )
        """
    )
    provider.execute(
        """
        CREATE TABLE tags (id TEXT PRIMARY KEY, name TEXT)
        """
    )
    provider.execute(
        """
        CREATE TABLE posttag (
            id TEXT PRIMARY KEY,
            post_id TEXT,
            tag_id TEXT
        )
        """
    )
    provider.execute("INSERT INTO users VALUES (?, ?)", ("u1", "Ada"))
    provider.execute("INSERT INTO users VALUES (?, ?)", ("u2", "Bob"))
    provider.execute(
        "INSERT INTO posts VALUES (?, ?, ?)", ("p1", "u1", "Hello")
    )
    provider.execute(
        "INSERT INTO posts VALUES (?, ?, ?)", ("p2", "u1", "World")
    )
    provider.execute(
        "INSERT INTO posts VALUES (?, ?, ?)", ("p3", "u2", "Other")
    )
    provider.execute("INSERT INTO tags VALUES (?, ?)", ("t1", "py"))
    provider.execute("INSERT INTO tags VALUES (?, ?)", ("t2", "sql"))
    provider.execute(
        "INSERT INTO posttag VALUES (?, ?, ?)", ("x1", "p1", "t1")
    )
    provider.execute(
        "INSERT INTO posttag VALUES (?, ?, ?)", ("x2", "p1", "t2")
    )
    yield provider
    provider.close()


def test_belongs_to_and_has_many_eager(db):
    registry = RelationRegistry()
    registry.register(
        "Post",
        RelationDefinition(
            kind="belongs_to",
            name="author",
            model="User",
            related_table="users",
            foreign_key="user_id",
            local_key="id",
        ),
    )
    registry.register(
        "User",
        RelationDefinition(
            kind="has_many",
            name="posts",
            model="Post",
            related_table="posts",
            foreign_key="user_id",
            local_key="id",
        ),
    )

    posts = (
        QueryBuilder(db, "posts", model="Post", relation_registry=registry)
        .with_("author")
        .order_by("id")
        .get()
    )
    assert posts[0]["author"]["name"] == "Ada"
    assert posts[2]["author"]["name"] == "Bob"

    users = (
        QueryBuilder(db, "users", model="User", relation_registry=registry)
        .with_("posts")
        .where("id", "u1")
        .get()
    )
    assert len(users[0]["posts"]) == 2


def test_belongs_to_many(db):
    registry = RelationRegistry()
    registry.register(
        "Post",
        RelationDefinition(
            kind="belongs_to_many",
            name="tags",
            model="Tag",
            related_table="tags",
            foreign_key="post_id",
            local_key="id",
            through_table="posttag",
            pivot_foreign_key="post_id",
            pivot_related_key="tag_id",
        ),
    )
    posts = (
        QueryBuilder(db, "posts", model="Post", relation_registry=registry)
        .with_("tags")
        .where("id", "p1")
        .get()
    )
    names = {t["name"] for t in posts[0]["tags"]}
    assert names == {"py", "sql"}
