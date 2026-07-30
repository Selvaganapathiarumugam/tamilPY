"""Sample helpdesk seed."""

from uuid import uuid4

from tpy.database import Seeder


class HelpdeskSeeder(Seeder):
    """Insert one demo category when empty."""

    def run(self) -> None:
        try:
            existing = self.db.fetch_one("SELECT id FROM category LIMIT 1")
        except Exception:
            return
        if existing is not None:
            return
        self.db.execute(
            "INSERT INTO category (id, name, description) VALUES (?, ?, ?)",
            (str(uuid4()), "General", "Default support category"),
        )
