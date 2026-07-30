from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from tpy.providers.base import BaseProvider


class MongoProvider(BaseProvider):
    """
    MongoDB provider powered by PyMongo.

    Generated Mongo repositories use collection helpers directly. Migration
    files are shared with SQL providers, but this provider applies their
    operations as collection creation and index creation instead of SQL.
    """

    def __init__(
        self,
        database_url: str | None = None,
        project_root: Path | str = ".",
    ) -> None:
        super().__init__(database_url, project_root)
        self.client: Any = None

    def connect(self):
        """Open a PyMongo database handle."""
        if self.connection is not None:
            return self.connection

        if not self.database_url:
            raise ValueError(
                "DATABASE_URL is required for the mongodb provider."
            )

        from pymongo import MongoClient
        from pymongo.uri_parser import parse_uri

        parsed = parse_uri(self.database_url)
        database_name = parsed.get("database") or "tpy"
        options = {
            str(key).lower()
            for key in (parsed.get("options") or {})
        }
        kwargs = {}
        if "serverselectiontimeoutms" not in options:
            kwargs["serverSelectionTimeoutMS"] = 5000

        self.client = MongoClient(self.database_url, **kwargs)
        self.client.admin.command("ping")
        self.connection = self.client[database_name]
        return self.connection

    def close(self) -> None:
        """Close the PyMongo client."""
        if self.client is not None:
            self.client.close()
        self.client = None
        self.connection = None

    def execute(self, sql: str, params=None):
        raise NotImplementedError(
            "MongoDB provider does not execute SQL statements. "
            "Use collection helpers or generated Mongo repositories."
        )

    def fetch_all(self, sql: str, params=None):
        raise NotImplementedError(
            "MongoDB provider does not execute SQL statements. "
            "Use collection helpers or generated Mongo repositories."
        )

    def fetch_one(self, sql: str, params=None):
        raise NotImplementedError(
            "MongoDB provider does not execute SQL statements. "
            "Use collection helpers or generated Mongo repositories."
        )

    def ensure_migrations_table(self) -> None:
        """Create a unique migration-name index."""
        db = self.connect()
        db["_tpy_migrations"].create_index("name", unique=True)

    def is_applied(self, name: str) -> bool:
        """Return whether a migration name has already been recorded."""
        db = self.connect()
        return db["_tpy_migrations"].find_one({"name": name}) is not None

    def record_migration(self, name: str) -> None:
        """Record a successful migration."""
        db = self.connect()
        db["_tpy_migrations"].insert_one(
            {
                "name": name,
                "applied_at": datetime.now(UTC),
            }
        )

    def remove_migration(self, name: str) -> None:
        """Remove a migration record after rollback."""
        db = self.connect()
        db["_tpy_migrations"].delete_one({"name": name})

    def latest_migration(self) -> str | None:
        """Return the most recently applied migration name."""
        db = self.connect()
        row = db["_tpy_migrations"].find_one(sort=[("applied_at", -1)])
        return row["name"] if row is not None else None

    def migrate(self) -> list[str]:
        """
        Apply pending migrations as MongoDB collections and indexes.

        Returns:
            List of applied migration module names.
        """
        self.connect()
        self.ensure_migrations_table()

        applied: list[str] = []
        for path in self.migration_files():
            name = path.stem
            if self.is_applied(name):
                continue

            migration = self.load_migration(path)
            migration.up()
            self.apply_operations(migration.operations)
            self.record_migration(name)
            applied.append(name)

        return applied

    def rollback(self) -> str | None:
        """
        Roll back the latest applied migration.

        Returns:
            Rolled-back migration name, or ``None`` when nothing to roll back.
        """
        self.connect()
        self.ensure_migrations_table()

        latest = self.latest_migration()
        if latest is None:
            return None

        path = self.migrations_path / f"{latest}.py"
        if not path.exists():
            return None

        migration = self.load_migration(path)
        migration.down()
        self.apply_operations(migration.operations)
        self.remove_migration(latest)
        return latest

    def apply_operations(self, operations: list[dict]) -> None:
        """Apply collected migration operations to MongoDB."""
        db = self.connect()
        current_collection: str | None = None

        for operation in operations:
            action = operation["action"]

            if action == "create_table":
                current_collection = operation["table"]
                if current_collection not in db.list_collection_names():
                    db.create_collection(current_collection)
                continue

            if action == "column":
                if current_collection is None:
                    continue
                column = operation["column"]
                options = column.options
                if options.get("primary") or options.get("unique"):
                    db[current_collection].create_index(
                        column.name,
                        unique=True,
                    )
                elif options.get("index") or options.get("references"):
                    db[current_collection].create_index(column.name)
                continue

            if action == "drop_table":
                db.drop_collection(operation["table"])
                current_collection = None

    def collection_all(self, collection: str) -> list[dict]:
        """Return every document from a collection."""
        db = self.connect()
        return [
            self.normalize_document(document)
            for document in db[collection].find()
        ]

    def collection_find_one(
        self,
        collection: str,
        filters: dict,
    ) -> dict | None:
        """Return a single normalized document."""
        db = self.connect()
        document = db[collection].find_one(self.serialize_document(filters))
        if document is None:
            return None
        return self.normalize_document(document)

    def collection_insert_one(
        self,
        collection: str,
        document: dict,
    ) -> Any:
        """Insert a document."""
        db = self.connect()
        return db[collection].insert_one(self.serialize_document(document))

    def collection_update_one(
        self,
        collection: str,
        filters: dict,
        updates: dict,
    ) -> Any:
        """Update one document with ``$set``."""
        db = self.connect()
        return db[collection].update_one(
            self.serialize_document(filters),
            {"$set": self.serialize_document(updates)},
        )

    def collection_delete_one(
        self,
        collection: str,
        filters: dict,
    ) -> bool:
        """Delete one document and return whether a document was removed."""
        db = self.connect()
        result = db[collection].delete_one(self.serialize_document(filters))
        return result.deleted_count > 0

    def serialize_document(self, value):
        """Convert Python values that PyMongo should store as strings."""
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, dict):
            return {
                key: self.serialize_document(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self.serialize_document(item) for item in value]
        return value

    def normalize_document(self, document: dict) -> dict:
        """Remove Mongo's internal ``_id`` and stringify UUID values."""
        normalized = dict(document)
        normalized.pop("_id", None)
        return self.serialize_document(normalized)
