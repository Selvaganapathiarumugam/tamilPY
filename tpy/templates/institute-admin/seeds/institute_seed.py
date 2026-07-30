"""Sample institute seed."""

from uuid import uuid4

from tpy.database import Seeder


class InstituteSeeder(Seeder):
    """Insert one demo teacher when empty."""

    def run(self) -> None:
        try:
            existing = self.db.fetch_one("SELECT id FROM teacher LIMIT 1")
        except Exception:
            return
        if existing is not None:
            return
        self.db.execute(
            "INSERT INTO teacher (id, name, subject) VALUES (?, ?, ?)",
            (str(uuid4()), "Ada Lovelace", "Mathematics"),
        )
