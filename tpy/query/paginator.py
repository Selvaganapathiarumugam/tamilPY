"""
Length-aware pagination result for Query Builder.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LengthAwarePaginator:
    """Paginated query result with total count metadata."""

    items: list[dict[str, Any]]
    total: int
    page: int
    per_page: int

    @property
    def last_page(self) -> int:
        """Return the last page number (minimum 1)."""
        if self.per_page <= 0:
            return 1
        return max(1, (self.total + self.per_page - 1) // self.per_page)

    def to_dict(self) -> dict[str, Any]:
        """Serialize pagination envelope for API responses."""
        return {
            "data": self.items,
            "meta": {
                "total": self.total,
                "page": self.page,
                "per_page": self.per_page,
                "last_page": self.last_page,
            },
        }
