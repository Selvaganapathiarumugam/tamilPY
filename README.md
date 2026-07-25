Schema-driven Python web framework by **Selvaganapathi Arumugam**.

## Install

```bash
pip install tamilPY
```

## Client flow

1. `tpy new myapp` — create the app  
2. Edit `schema.tpy` — define models  
3. `tpy build` — choose DB (SQLite / PostgreSQL / MySQL / MongoDB), enter connection details, generate code  
4. `tpy migrate` — apply migrations  
5. `tpy seed` — seed sample data  
6. `tpy serve` — run the API  

## Commands

| Command | Description |
|---------|-------------|
| `tpy new <name>` | Create a new project |
| `tpy build` | Interactive DB setup + generate app layers |
| `tpy build --skip-db` | Generate using existing `.env` |
| `tpy crud` | Regenerate CRUD layers from `schema.tpy` |
| `tpy db configure` | Re-run DB wizard anytime |
| `tpy migrate` | Create DB if needed + apply migrations |
| `tpy migrate rollback` | Roll back latest migration |
| `tpy seed` | Run `database/seeds` |
| `tpy serve` | Start FastAPI server |
| `tpy doctor` | Validate project structure |
| `tpy version` | Show framework version |

## schema.tpy reference

```tpy
database postgres

model User {
  id: uuid primary
  email: string unique required
}

model Post {
  id: uuid primary
  title: string required index
  body: string nullable
  user_id: uuid references User
  status: string default "draft"
  published: bool default false
  views: int default 0
}
```

### Types

`int` · `string` · `float` · `bool` · `uuid` · `datetime`

### Field constraints

| Constraint | Effect |
|------------|--------|
| `primary` | Primary key |
| `required` | Required in the create API |
| `unique` | `UNIQUE` column |
| `nullable` | Allows `NULL` / optional |
| `index` | Generates `CREATE INDEX idx_<table>_<column>` |
| `default <value>` | Column default (number, `"string"`, `true`/`false`) |
| `references <Model>` | Foreign key (alias: `foreign <Model>`) |

### Foreign keys

Use `references <Model>` on a field. It targets the referenced model's `id` by
default, or a specific column with `references <Model>.<column>`:

```tpy
user_id: uuid references User
author:  uuid references User.id
```

Compiles to `REFERENCES "user" ("id")`. Define the referenced model **earlier**
in `schema.tpy` so its migration runs first.

### Defaults & indexes

- Fields with a `default` become optional in the generated create schema.
- `index` adds a secondary index; primary keys are already indexed.

## Docs

Open [TamilPY](https://selvaganapathiarumugam.github.io/tamilPY/) for the full client guide.

## Release (PyPI)

Publishing is automated from the **Production** branch via GitHub Actions.

1. In GitHub → **Settings → Secrets and variables → Actions**, add:
   - Name: `PYPI_API_TOKEN`
   - Value: your PyPI API token (`pypi-...`)
2. Merge your work into `Production`.
3. Create and push a version tag from that commit:

```bash
git checkout Production
git pull
git tag v0.1.7
git push origin v0.1.7
```

The workflow will:
- verify the tag is on `Production`
- update `pyproject.toml` version from the tag
- build `dist/` (sdist + wheel)
- upload to PyPI

## Author

**Selvaganapathi Arumugam**  
Software Developer
