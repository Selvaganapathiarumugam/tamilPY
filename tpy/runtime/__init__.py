"""TPY runtime exports."""

_EXPORTS = {
    "BaseModel": ("tpy.runtime.base_model", "BaseModel"),
    "Builder": ("tpy.runtime.builder", "Builder"),
    "Logger": ("tpy.runtime.logger", "Logger"),
    "LogLevel": ("tpy.runtime.logger", "LogLevel"),
    "Request": ("tpy.runtime.request", "Request"),
    "Response": ("tpy.runtime.response", "Response"),
    "Route": ("tpy.runtime.routing", "Route"),
    "Router": ("tpy.runtime.routing", "Router"),
    "TemplateEngine": ("tpy.runtime.template_engine", "TemplateEngine"),
    "ValidationError": ("tpy.runtime.validation", "ValidationError"),
    "Validator": ("tpy.runtime.validation", "Validator"),
    "get_logger": ("tpy.runtime.logger", "get_logger"),
    "validate": ("tpy.runtime.validation", "validate"),
}

__all__ = [
    "BaseModel",
    "Builder",
    "Logger",
    "LogLevel",
    "Request",
    "Response",
    "Route",
    "Router",
    "TemplateEngine",
    "ValidationError",
    "Validator",
    "get_logger",
    "validate",
]


def __getattr__(name: str):
    """Load runtime exports on demand to avoid circular imports."""
    if name not in _EXPORTS:
        raise AttributeError(f"module 'tpy.runtime' has no attribute {name!r}")

    module_name, attribute = _EXPORTS[name]
    module = __import__(module_name, fromlist=[attribute])
    value = getattr(module, attribute)
    globals()[name] = value
    return value
