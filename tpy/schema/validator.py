"""Semantic validation for parsed ``schema.tpy`` programs."""

from __future__ import annotations

from tpy.parser.ast import FieldNode, ModelNode, ProgramNode
from tpy.schema.errors import SchemaDiagnostic, SchemaValidationError

_KNOWN_TYPES = frozenset(
    {"int", "string", "float", "bool", "uuid", "datetime", "enum"}
)
_KNOWN_CONSTRAINTS = frozenset(
    {"primary", "required", "unique", "nullable", "index"}
)


def validate_program(
    program: ProgramNode,
    *,
    filename: str = "schema.tpy",
    raise_on_error: bool = False,
) -> list[SchemaDiagnostic]:
    """
    Run semantic checks on ``program`` and return diagnostics.

    Args:
        program: Parsed schema AST.
        filename: Path shown in diagnostic messages.
        raise_on_error: When True, raise ``SchemaValidationError`` if any
            error-severity diagnostics exist.
    """
    diagnostics: list[SchemaDiagnostic] = []
    model_names = [model.name for model in program.models]
    enum_names = {enum.name for enum in program.enums}

    _check_duplicate_models(program, filename, diagnostics)
    for model in program.models:
        _check_duplicate_fields(model, filename, diagnostics)
        _check_fields(model, model_names, enum_names, filename, diagnostics)
        _check_unique_together(model, filename, diagnostics)
        _check_relations(model, model_names, filename, diagnostics)

    _check_circular_required_refs(program, filename, diagnostics)

    if raise_on_error and any(d.severity == "error" for d in diagnostics):
        raise SchemaValidationError(diagnostics)
    return diagnostics


def _line(value: int | None) -> int:
    return value if value is not None else 1


def _check_duplicate_models(
    program: ProgramNode,
    filename: str,
    diagnostics: list[SchemaDiagnostic],
) -> None:
    seen: dict[str, int] = {}
    for model in program.models:
        if model.name in seen:
            diagnostics.append(
                SchemaDiagnostic(
                    line=_line(model.line),
                    message=f"duplicate model name '{model.name}'",
                    filename=filename,
                )
            )
        else:
            seen[model.name] = _line(model.line)


def _check_duplicate_fields(
    model: ModelNode,
    filename: str,
    diagnostics: list[SchemaDiagnostic],
) -> None:
    seen: set[str] = set()
    for field in model.fields:
        if field.name in seen:
            diagnostics.append(
                SchemaDiagnostic(
                    line=_line(field.line),
                    message=(
                        f"duplicate field name '{field.name}' "
                        f"in model '{model.name}'"
                    ),
                    filename=filename,
                )
            )
        else:
            seen.add(field.name)


def _check_fields(
    model: ModelNode,
    model_names: list[str],
    enum_names: set[str],
    filename: str,
    diagnostics: list[SchemaDiagnostic],
) -> None:
    known_models = set(model_names)
    for field in model.fields:
        _check_field_type(field, enum_names, filename, diagnostics)
        for constraint in field.constraints:
            if constraint not in _KNOWN_CONSTRAINTS:
                diagnostics.append(
                    SchemaDiagnostic(
                        line=_line(field.line),
                        message=(
                            f"unknown constraint '{constraint}' "
                            f"on field '{field.name}'"
                        ),
                        filename=filename,
                    )
                )
        if field.reference is not None:
            target = field.reference.model
            if target not in known_models:
                diagnostics.append(
                    SchemaDiagnostic(
                        line=_line(field.reference.line or field.line),
                        message=(
                            f"field '{field.name}' references undefined "
                            f"model '{target}'"
                        ),
                        hint=_suggestion(target, model_names),
                        filename=filename,
                    )
                )


def _check_field_type(
    field: FieldNode,
    enum_names: set[str],
    filename: str,
    diagnostics: list[SchemaDiagnostic],
) -> None:
    datatype = field.datatype
    if datatype == "enum":
        return
    if datatype.startswith("enum:"):
        name = datatype.split(":", 1)[1]
        if name not in enum_names:
            diagnostics.append(
                SchemaDiagnostic(
                    line=_line(field.line),
                    message=(
                        f"field '{field.name}' references undefined "
                        f"enum '{name}'"
                    ),
                    hint=_suggestion(name, sorted(enum_names)),
                    filename=filename,
                )
            )
        return
    if datatype not in _KNOWN_TYPES:
        diagnostics.append(
            SchemaDiagnostic(
                line=_line(field.line),
                message=f"unknown type '{datatype}' on field '{field.name}'",
                filename=filename,
            )
        )


def _check_unique_together(
    model: ModelNode,
    filename: str,
    diagnostics: list[SchemaDiagnostic],
) -> None:
    field_names = {field.name for field in model.fields}
    lines = model.unique_together_lines or [None] * len(model.unique_together)
    for index, columns in enumerate(model.unique_together):
        line = lines[index] if index < len(lines) else model.line
        for column in columns:
            if column not in field_names:
                diagnostics.append(
                    SchemaDiagnostic(
                        line=_line(line),
                        message=(
                            f"unique(...) references nonexistent field "
                            f"'{column}' in model '{model.name}'"
                        ),
                        filename=filename,
                    )
                )


def _check_relations(
    model: ModelNode,
    model_names: list[str],
    filename: str,
    diagnostics: list[SchemaDiagnostic],
) -> None:
    known = set(model_names)
    for relation in model.relations:
        if relation.model not in known:
            diagnostics.append(
                SchemaDiagnostic(
                    line=_line(relation.line),
                    message=(
                        f"relation '{relation.name}' references undefined "
                        f"model '{relation.model}'"
                    ),
                    hint=_suggestion(relation.model, model_names),
                    filename=filename,
                )
            )
        if relation.kind == "belongs_to_many":
            if not relation.through:
                diagnostics.append(
                    SchemaDiagnostic(
                        line=_line(relation.line),
                        message=(
                            f"belongs_to_many '{relation.name}' requires "
                            f"'through PivotModel'"
                        ),
                        filename=filename,
                    )
                )
            elif relation.through not in known:
                diagnostics.append(
                    SchemaDiagnostic(
                        line=_line(relation.line),
                        message=(
                            f"belongs_to_many '{relation.name}' through "
                            f"undefined model '{relation.through}'"
                        ),
                        hint=_suggestion(relation.through, model_names),
                        filename=filename,
                    )
                )


def _check_circular_required_refs(
    program: ProgramNode,
    filename: str,
    diagnostics: list[SchemaDiagnostic],
) -> None:
    """Warn when two models have required FKs pointing at each other."""
    required_edges: dict[str, set[str]] = {}
    for model in program.models:
        targets: set[str] = set()
        for field in model.fields:
            if field.reference is None:
                continue
            if "required" not in field.constraints:
                continue
            targets.add(field.reference.model)
        required_edges[model.name] = targets

    reported: set[tuple[str, str]] = set()
    for source, targets in required_edges.items():
        for target in targets:
            if source in required_edges.get(target, set()):
                pair = tuple(sorted((source, target)))
                if pair in reported:
                    continue
                reported.add(pair)
                model = next(m for m in program.models if m.name == source)
                diagnostics.append(
                    SchemaDiagnostic(
                        line=_line(model.line),
                        message=(
                            f"circular required references between "
                            f"'{pair[0]}' and '{pair[1]}'"
                        ),
                        severity="warning",
                        filename=filename,
                    )
                )


def _suggestion(name: str, candidates: list[str]) -> str | None:
    if not candidates:
        return None
    best = None
    best_distance = None
    for candidate in candidates:
        distance = _edit_distance(name.lower(), candidate.lower())
        if best_distance is None or distance < best_distance:
            best = candidate
            best_distance = distance
    if best is None or best_distance is None or best_distance > 3:
        return None
    return f"did you mean '{best}'?"


def _edit_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    prev = list(range(len(right) + 1))
    for i, a in enumerate(left, start=1):
        current = [i]
        for j, b in enumerate(right, start=1):
            insert = current[j - 1] + 1
            delete = prev[j] + 1
            replace = prev[j - 1] + (0 if a == b else 1)
            current.append(min(insert, delete, replace))
        prev = current
    return prev[-1]
