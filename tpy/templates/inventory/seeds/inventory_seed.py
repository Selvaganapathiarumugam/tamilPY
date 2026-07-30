"""Sample inventory seed."""

from uuid import uuid4

from tpy.database import Seeder


class InventorySeeder(Seeder):
    """Insert one demo warehouse when empty."""

    def run(self) -> None:
        try:
            existing = self.db.fetch_one("SELECT id FROM warehouse LIMIT 1")
        except Exception:
            return
        if existing is not None:
            return
        self.db.execute(
            "INSERT INTO warehouse (id, name, location) VALUES (?, ?, ?)",
            (str(uuid4()), "Main Depot", "Chennai"),
        )
