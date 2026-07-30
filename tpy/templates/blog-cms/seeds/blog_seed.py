"""Sample blog CMS seed."""

from uuid import uuid4

from tpy.database import Seeder


class BlogSeeder(Seeder):
    """Insert one demo author when empty."""

    def run(self) -> None:
        try:
            existing = self.db.fetch_one("SELECT id FROM author LIMIT 1")
        except Exception:
            return
        if existing is not None:
            return
        self.db.execute(
            "INSERT INTO author (id, name, email, bio) VALUES (?, ?, ?, ?)",
            (str(uuid4()), "Editor", "editor@example.com", "Site editor"),
        )
