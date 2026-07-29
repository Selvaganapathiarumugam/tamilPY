"""
Minimal 5-field cron expression matcher (no external dependency).
"""

from __future__ import annotations

from datetime import datetime

from tpy.schedule.exceptions import ScheduleError


class CronExpression:
    """
    Match datetimes against a standard 5-field cron string.

    Fields: ``minute hour day-of-month month day-of-week``
    Supports ``*``, ``N``, ``A-B``, ``*/N``, and comma lists.
    Day-of-week: ``0``/``7`` = Sunday … ``6`` = Saturday.
    """

    def __init__(self, expression: str) -> None:
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ScheduleError(
                f"Cron expression must have 5 fields, got {len(parts)}: "
                f"{expression!r}"
            )
        self.expression = expression.strip()
        self.minute = parts[0]
        self.hour = parts[1]
        self.day = parts[2]
        self.month = parts[3]
        self.weekday = parts[4]

    def is_due(self, moment: datetime) -> bool:
        """Return whether ``moment`` matches this expression."""
        return (
            self._match(self.minute, moment.minute, 0, 59)
            and self._match(self.hour, moment.hour, 0, 23)
            and self._match(self.day, moment.day, 1, 31)
            and self._match(self.month, moment.month, 1, 12)
            and self._match_weekday(self.weekday, moment.weekday())
        )

    def _match_weekday(self, field: str, python_weekday: int) -> bool:
        # Python: Mon=0 … Sun=6 → cron: Sun=0 … Sat=6
        cron_weekday = (python_weekday + 1) % 7
        return self._match(field, cron_weekday, 0, 7, wrap_seven=True)

    def _match(
        self,
        field: str,
        value: int,
        minimum: int,
        maximum: int,
        wrap_seven: bool = False,
    ) -> bool:
        for piece in field.split(","):
            if self._match_piece(piece, value, minimum, maximum, wrap_seven):
                return True
        return False

    def _match_piece(
        self,
        piece: str,
        value: int,
        minimum: int,
        maximum: int,
        wrap_seven: bool,
    ) -> bool:
        piece = piece.strip()
        if piece == "*":
            return True

        if piece.startswith("*/"):
            step = int(piece[2:])
            if step <= 0:
                raise ScheduleError(f"Invalid cron step: {piece}")
            return (value - minimum) % step == 0

        if "-" in piece:
            start_s, end_s = piece.split("-", 1)
            start, end = int(start_s), int(end_s)
            if wrap_seven and end == 7:
                end = 0
                return value == start or value == 0 or start <= value <= 6
            return start <= value <= end

        number = int(piece)
        if wrap_seven and number == 7:
            number = 0
        return value == number
