"""
Raw SQL / expression escape hatch for the Query Builder.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class Raw:
    """
    Unvalidated SQL fragment.

    Values must still use placeholders; never interpolate user input into
    ``sql``.
    """

    sql: str
    params: Sequence[Any] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "params", tuple(self.params))
