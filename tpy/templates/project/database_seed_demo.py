"""
Example database seed.

Edit this file (or add more seed modules) and run: tpy seed
"""

from uuid import uuid4

from tpy.database import Seeder


class DemoSeeder(Seeder):
    """
    Inserts a sample User row when the ``user`` table exists.
    """

    def run(self) -> None:
        try:
            existing = self.db.fetch_one(
                "SELECT id FROM user LIMIT 1"
            )
        except Exception:
            return

        if existing is not None:
            return

        self.db.execute(
            "INSERT INTO user (id, name, email, age) VALUES (?, ?, ?, ?)",
            (str(uuid4()), "Demo User", "demo@example.com", 25),
        )
