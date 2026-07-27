# TamilPY

**Schema-driven Python web framework** — define models in `schema.tpy`, generate a production-ready FastAPI stack, and ship.

Built by [Selvaganapathi Arumugam](https://github.com/selvaganapathiarumugam).

[Documentation](https://selvaganapathiarumugam.github.io/tamilPY/) · [PyPI](https://pypi.org/project/tamilPY/) · Requires Python 3.12+

---

## Features

- **Schema-first development** — one `schema.tpy` drives models, migrations, repositories, services, controllers, and routes
- **Multi-database** — SQLite, PostgreSQL, MySQL, and MongoDB
- **Full CRUD generation** — FastAPI layers from a single build step
- **Admin dashboard** — optional Vite + React UI generated from the same schema
- **CLI workflow** — project scaffolding, migrations, seeds, and local server in one tool

---

## Installation

```bash
pip install tamilPY
```

Verify the install:

```bash
tpy version
```

---

## Quick start

```bash
tpy new myapp
cd myapp
```

Edit `schema.tpy`, then:

```bash
tpy build          # configure database + generate application layers
tpy migrate        # apply migrations
tpy seed           # optional sample data
tpy serve          # start the API at http://127.0.0.1:8000
```

Generate the admin UI (optional):

```bash
tpy admin          # or: tpy build --with-ui
cd admin && npm install && npm run dev
```

Admin UI: `http://127.0.0.1:5173`

---

## CLI reference

| Command | Description |
|---------|-------------|
| `tpy new <name>` | Create a new project |
| `tpy build` | Interactive database setup and code generation |
| `tpy build --skip-db` | Generate using an existing `.env` |
| `tpy build --with-ui` | Generate app layers and the React admin dashboard |
| `tpy crud` | Regenerate CRUD layers from `schema.tpy` |
| `tpy admin` | Generate a Vite + React admin dashboard |
| `tpy db configure` | Re-run the database configuration wizard |
| `tpy migrate` | Create the database (if needed) and apply migrations |
| `tpy migrate rollback` | Roll back the latest migration |
| `tpy seed` | Run seed scripts in `database/seeds` |
| `tpy serve` | Start the FastAPI development server |
| `tpy doctor` | Validate project structure |
| `tpy version` | Print the installed framework version |

---

## Schema language

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
| `required` | Required on create |
| `unique` | Unique column constraint |
| `nullable` | Allows `NULL` / optional values |
| `index` | Secondary index (`idx_<table>_<column>`) |
| `default <value>` | Column default (`0`, `"draft"`, `true` / `false`) |
| `references <Model>` | Foreign key (alias: `foreign <Model>`) |

### Foreign keys

```tpy
user_id: uuid references User
author:  uuid references User.id
```

Compiles to `REFERENCES "user" ("id")`. Define referenced models **before** dependents so migrations run in order.

### Defaults and indexes

- Fields with `default` are optional in the generated create schema
- `index` adds a secondary index; primary keys are indexed automatically

---

## Admin dashboard

`tpy admin` generates a Vite + React app under `admin/` from `schema.tpy`.

```bash
tpy serve          # terminal 1 — API
tpy admin          # generate UI (once, or after schema changes)
cd admin
npm install
npm run dev        # terminal 2 — UI
```

The wizard prompts for the API base URL (default: `http://127.0.0.1:8000`).

| Path | Role |
|------|------|
| `src/data/models.js` | Model registry generated from `schema.tpy` |
| `src/components/` | Shared Layout, DataTable, RecordForm |
| `src/pages/` | Generic list and form pages |

Re-running `tpy admin` refreshes generated files to match the current schema.

> **Note:** The admin `package.json` uses `@rollup/wasm-node` so Vite works on Windows hosts where Application Control blocks Rollup’s native binary.

---

## Documentation

Full client guide: [TamilPY Docs](https://selvaganapathiarumugam.github.io/tamilPY/)

---

## License

MIT © Selvaganapathi Arumugam
