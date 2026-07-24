from tpy.providers.base import BaseProvider


class MongoProvider(BaseProvider):
    """
    MongoDB provider stub.

    Relational migration SQL is not supported. Use indexes/collections APIs
    in a future iteration.
    """

    def connect(self):
        """Connect using Motor when DATABASE_URL is configured."""
        if self.connection is not None:
            return self.connection

        if not self.database_url:
            raise ValueError(
                "DATABASE_URL is required for the mongodb provider."
            )

        from motor.motor_asyncio import AsyncIOMotorClient

        self.connection = AsyncIOMotorClient(self.database_url)
        return self.connection

    def execute(self, sql: str, params=None):
        raise NotImplementedError(
            "MongoDB provider does not execute SQL statements."
        )

    def fetch_all(self, sql: str, params=None):
        raise NotImplementedError(
            "MongoDB provider does not execute SQL statements."
        )

    def fetch_one(self, sql: str, params=None):
        raise NotImplementedError(
            "MongoDB provider does not execute SQL statements."
        )

    def migrate(self):
        raise NotImplementedError(
            "MongoDB migrations are not implemented yet."
        )

    def rollback(self):
        raise NotImplementedError(
            "MongoDB rollback is not implemented yet."
        )
