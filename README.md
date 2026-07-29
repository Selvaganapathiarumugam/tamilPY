# TamilPY

[![PyPI version](https://img.shields.io/pypi/v/tamilPY.svg)](https://pypi.org/project/tamilPY/)
[![Python versions](https://img.shields.io/pypi/pyversions/tamilPY.svg)](https://pypi.org/project/tamilPY/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Schema-driven Python web framework** — define models in `schema.tpy`, generate a production-ready FastAPI stack, and ship.

Built by [Selvaganapathi Arumugam](https://github.com/selvaganapathiarumugam).

[Documentation](https://selvaganapathiarumugam.github.io/tamilPY/) · [PyPI](https://pypi.org/project/tamilPY/) · Requires Python 3.12+

---

## Why "tamilPY"?

The name is a nod to my mother tongue, Tamil — a small personal tribute from the author. The framework itself isn't Tamil-specific in any way; it's a general-purpose, schema-driven Python web framework built for any project, any language, any team.

---

## Table of contents

- [Features](#features)
- [How it compares](#how-it-compares)
- [Installation](#installation)
- [Quick start](#quick-start)
- [CLI reference](#cli-reference)
- [Schema language](#schema-language)
- [Admin dashboard](#admin-dashboard)
- [Documentation](#documentation)
- [License](#license)
- [Contributing](#contributing)

---

## Features

- **Schema-first development** — one `schema.tpy` drives models, migrations, repositories, services, controllers, and routes
- **Multi-database** — SQLite, PostgreSQL, MySQL, and MongoDB
- **Full CRUD generation** — FastAPI layers from a single build step
- **Query Builder & relationships** — fluent queries, schema `relations { }`, eager loading
- **Events, queues & scheduler** — sync event bus, background jobs, cron-style schedule
- **Cache, validation & API envelopes** — memory/file/Redis, pipe rules, `ApiResponse`
- **Kernel platform** — Application providers/plugins, middleware groups, health & lifecycle
- **Logging, config & storage** — log channels, config cache, file storage, route cache
- **DX tooling** — `tpy optimize`, richer CLI (`-V`, `about`), `tpy watch`
- **Admin dashboard** — optional Vite + React UI generated from the same schema
- **CLI workflow** — scaffolding, migrations, seeds, queue/schedule/cache, and local server

Full docs: [TamilPY Docs](https://selvaganapathiarumugam.github.io/tamilPY/)

---

## How it compares

| Criteria | Django | Flask | FastAPI (plain) | tamilPY |
|---|---|---|---|---|
| Development speed | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Learning curve | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Boilerplate code | High | Very high (build it yourself) | Moderate (routes/schemas written by hand) | Very low (schema-generated) |
| Code generation | ❌ | ❌ | ❌ | ✅ Full stack (models → routes → admin) |
| Database support | PostgreSQL, MySQL, SQLite, Oracle | Any (via extensions, e.g. SQLAlchemy) | Any (via extensions, e.g. SQLAlchemy, Tortoise) | SQLite, PostgreSQL, MySQL, MongoDB |
| REST API | Requires DRF | Manual | ✅ Native | ✅ FastAPI native |
| Async | Limited | ❌ | ✅ Native | ✅ Native |
| Type safety | Optional | Optional | ✅ Pydantic | ✅ Pydantic-enforced |
| Admin dashboard | ✅ Built-in | ❌ | ❌ | ✅ Generated (Vite + React) |
| CRUD development | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Time to MVP | Days / weeks | Weeks | Days | Hours to a few days |

*Ratings reflect typical experience for standard CRUD/API-driven projects; results vary by team familiarity and project scope.*

---

## Installation

```bash
pip install tamilPY
```

Database drivers are optional extras:

```bash
pip install "tamilPY[postgres]"
pip install "tamilPY[mysql]"
pip install "tamilPY[mongodb]"
pip install "tamilPY[redis]"
pip install "tamilPY[all]"
```

SQLite works with the base install (stdlib).

Verify the install:

```bash
python -m tpy.cli version
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

### JWT auth (optional)

```bash
tpy auth
pip install -r requirements.txt
tpy migrate
tpy seed
tpy serve
tpy admin   # refresh UI with login page
```

Default super-admin: `admin@example.com` / `admin123`  

Roles: `super-admin`, `admin`, `developer` — dashboard allows **super-admin** and **developer** only.

API: `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `GET /auth/me`

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
| `tpy auth` | Enable JWT auth (login/register/refresh/logout), AuthRole + User, role seeds |
| `tpy db configure` | Re-run the database configuration wizard |
| `tpy migrate` | Create the database (if needed) and apply migrations |
| `tpy migrate rollback` | Roll back the latest migration |
| `tpy seed` | Run seed scripts in `database/seeds` |
| `tpy queue table` | Create `_tpy_jobs` / failed-job tables |
| `tpy queue work` | Run a queue worker (`--driver database\|sync\|redis`) |
| `tpy schedule run` | Run due scheduled tasks |
| `tpy schedule list` | List registered schedule events |
| `tpy cache clear` | Flush file/memory/redis cache |
| `tpy config show \| cache \| status \| clear` | Inspect / cache configuration |
| `tpy route cache \| list \| clear` | Cache and list HTTP routes |
| `tpy optimize` | Cache config + routes for production |
| `tpy watch` | Rebuild when `schema.tpy` changes |
| `tpy about` | Framework + project environment |
| `tpy commands` | List CLI commands |
| `tpy serve` | Start the FastAPI development server |
| `tpy doctor` | Validate project structure |
| `tpy version` / `tpy -V` | Print the installed framework version |

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

`int` · `string` · `float` · `bool` · `uuid` · `datetime` · `enum(...)` / `enum Name`

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
| `on_delete` / `on_update` | FK actions: `cascade`, `set_null`, `restrict`, `no_action` |

Model-level composite unique:

```tpy
unique(student_id, course_id)
```

### Relationships (v0.1.9+)

```tpy
model Post {
  id: uuid primary
  user_id: uuid references User
  relations {
    belongs_to User as author via user_id
    has_many Comment as comments
    belongs_to_many Tag as tags through PostTag
  }
}
```

Named / inline enums:

```tpy
enum Status { draft published }
status: enum Status
kind: enum(a, b)
```

### Foreign keys

```tpy
user_id: uuid references User
author:  uuid references User.id
```

Compiles to `REFERENCES "user" ("id")`. Define referenced models **before** dependents so migrations run in order.

### Defaults and indexes

- Fields with `default` are optional in the generated create schema
- `index` adds a secondary index; primary keys are indexed automatically

### Database support

SQLite, PostgreSQL, MySQL, and MongoDB are supported for generated CRUD and migrations. SQL providers apply migrations as tables, columns, indexes, and foreign keys. MongoDB applies the same schema as collections and indexes; references are indexed metadata rather than enforced foreign-key constraints.

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

> **Note:** The admin `package.json` uses `@rollup/wasm-node` so Vite works on Windows hosts where Application Control blocks Rollup's native binary.

---

## Documentation

Full client & platform guide (GitHub Pages):

**[TamilPY Docs](https://selvaganapathiarumugam.github.io/tamilPY/)**

In-page sections: [Install](https://selvaganapathiarumugam.github.io/tamilPY/#install) · [Features](https://selvaganapathiarumugam.github.io/tamilPY/#features) · [Platform API](https://selvaganapathiarumugam.github.io/tamilPY/#platform) · [CLI](https://selvaganapathiarumugam.github.io/tamilPY/#commands)

Feature cards open **study guides**  with setup, how-it-works, examples, and common mistakes — for example:

- [Schema-first generation](https://selvaganapathiarumugam.github.io/tamilPY/schema.html)
- [ApiResponse helpers](https://selvaganapathiarumugam.github.io/tamilPY/api-response.html)
- [Query Builder & relations](https://selvaganapathiarumugam.github.io/tamilPY/query.html)
- [JWT auth](https://selvaganapathiarumugam.github.io/tamilPY/auth.html)
- [Optimize · CLI · Watch](https://selvaganapathiarumugam.github.io/tamilPY/cli-watch.html)

Also:

- [Schema grammar (v0.1)](https://github.com/Selvaganapathiarumugam/tamilPY/blob/Production/docs/schema-grammar.md)
- [Versioning & deprecation](https://github.com/Selvaganapathiarumugam/tamilPY/blob/Production/docs/versioning.md)
- [Changelog](https://github.com/Selvaganapathiarumugam/tamilPY/blob/Production/CHANGELOG.md)
- [Security policy](https://github.com/Selvaganapathiarumugam/tamilPY/blob/Production/SECURITY.md)

### Async / sync trade-off

Generated repositories and database providers are **synchronous**. FastAPI route
handlers call sync provider methods directly. That keeps the stack simple and
portable across SQLite / Postgres / MySQL / Mongo. For heavy IO under load,
run workers behind a process manager or plan for future async providers; do not
assume the generated DB layer is async-native today.

---

## Contributing

See [CONTRIBUTING.md](https://github.com/Selvaganapathiarumugam/tamilPY/blob/Production/CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](https://github.com/Selvaganapathiarumugam/tamilPY/blob/Production/CODE_OF_CONDUCT.md).

---

## License

MIT © Selvaganapathi Arumugam
