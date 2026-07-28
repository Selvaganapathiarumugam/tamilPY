"""
tamilPY exception hierarchy.
"""


class TpyError(Exception):
    """Base error for all tamilPY failures."""


class TpyParseError(TpyError):
    """Raised when ``schema.tpy`` cannot be lexed or parsed."""


class TpyConfigError(TpyError):
    """Raised for invalid project or environment configuration."""


class TpyProviderError(TpyError):
    """Raised for database provider / driver failures."""


class TpyGeneratorError(TpyError):
    """Raised when code generation fails."""
