"""Sample CRM seed (extend when ``tpy seed --fake`` is available)."""

from uuid import uuid4

from tpy.database import Seeder


class CrmSeeder(Seeder):
    """Insert one demo company when the table is empty."""

    def run(self) -> None:
        try:
            existing = self.db.fetch_one("SELECT id FROM company LIMIT 1")
        except Exception:
            return
        if existing is not None:
            return
        self.db.execute(
            "INSERT INTO company (id, name, industry) VALUES (?, ?, ?)",
            (str(uuid4()), "Acme Corp", "Software"),
        )
