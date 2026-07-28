# Contributing to tamilPY

Thanks for contributing! This guide keeps changes reviewable and aligned with the framework architecture.

## Development setup

```bash
git clone https://github.com/Selvaganapathiarumugam/tamilPY.git
cd tamilPY
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install -e ".[dev,all]"
```

If Windows Application Control blocks `tpy.exe`, use:

```bash
python -m tpy.cli --help
```

## Architecture rules

| Layer | Responsibility | Must NOT |
|-------|----------------|----------|
| Parser | `.tpy` → AST | Generate code |
| Generator | AST → templates → files | DB-specific SQL |
| Runtime | migrations, validation, routing helpers | Provider SQL |
| Provider | connections, SQL/Mongo, migrate | AST parsing |

Prefer existing utilities: `FileManager`, `TemplateEngine`, `ConfigLoader`, generators, providers.

## Workflow

1. Open an issue or discuss the change.
2. Keep PRs focused (one concern).
3. Add/adjust tests under `tests/`.
4. Run locally:

```bash
ruff check tpy tests
mypy tpy
pytest -q
```

5. Update `CHANGELOG.md` under `[Unreleased]` or the next version section.
6. Do not commit secrets (`.env`, `storage/auth_bootstrap.txt`).

## Code style

- Python 3.12+, type hints on public APIs, docstrings on public classes/methods.
- PEP 8 / Ruff formatting expectations.
- Templates only render data; business logic belongs in generators.

## Release notes

Maintainers bump the version in `pyproject.toml`, update `CHANGELOG.md`, merge to `Production`, and tag `vX.Y.Z` for Trusted Publishing to PyPI.
