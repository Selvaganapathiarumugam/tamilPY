"""Schema validation diagnostics and errors."""

from __future__ import annotations

from dataclasses import dataclass

from tpy.exceptions import TpyError


@dataclass(slots=True)
class SchemaDiagnostic:
    """A single schema validation finding with optional line number."""

    line: int
    message: str
    severity: str = "error"
    hint: str | None = None
    filename: str = "schema.tpy"

    def format(self) -> str:
        """
        Format as ``schema.tpy:<line> — <message> (hint)``.
        """
        text = f"{self.filename}:{self.line} — {self.message}"
        if self.hint:
            text = f"{text} ({self.hint})"
        return text


class SchemaValidationError(TpyError):
    """Raised when schema semantic validation finds one or more errors."""

    def __init__(self, diagnostics: list[SchemaDiagnostic]) -> None:
        self.diagnostics = diagnostics
        errors = [d for d in diagnostics if d.severity == "error"]
        message = "\n".join(d.format() for d in errors) or "Schema validation failed"
        super().__init__(message)
