# Changelog

All notable changes to **TamilPY Framework** are documented in this file.

---

## [0.1.9] - 2026-07-29

Schema-driven FastAPI platform release: Query Builder through watch mode (Features 1–20), richer CLI, and a professional GitHub Pages study-guide docs site.

**Docs:** [TamilPY Docs](https://selvaganapathiarumugam.github.io/tamilPY/) · [Platform guides](https://selvaganapathiarumugam.github.io/tamilPY/#platform)

### Added — runtime platform

- **Query Builder** (`tpy.query`): fluent, parameterized queries on `BaseProvider`; SQLite / Postgres / MySQL grammars; Mongo helpers; pagination.
- **ORM relationships**: `relations { }` in `schema.tpy` (`belongs_to`, `has_many`, `has_one`, `belongs_to_many`); eager load via `with_()` / `EagerLoader`.
- **Events** (`tpy.events`): sync `Event` / `Listener` / `EventDispatcher` (stop propagation, wildcards, process singleton).
- **Queue** (`tpy.queue`): `Job`, `Worker`; drivers `sync`, `database` (`_tpy_jobs`), `redis` (optional). CLI: `tpy queue table`, `tpy queue work`.
- **Scheduler** (`tpy.schedule`): cadence helpers, `app/schedule.py` `register()`, overlap locks. CLI: `tpy schedule run`, `tpy schedule list`.
- **Cache** (`tpy.cache`): `MemoryStore`, `FileStore`, `RedisStore`. CLI: `tpy cache clear`.
- **API responses** (`tpy.http.ApiResponse`): uniform JSON envelopes (`success`, `created`, `paginated`, `error`, `validation_error`, `not_found`, …).
- **Validation** (`tpy.validation`): pipe-rule `validate()` / `Validator` with `ValidationException`.
- **Application kernel** (`tpy.kernel`): dual-mode `Application` (`create()` / `mount()`), `Container`, `ServiceProvider`, plugins.
- **Middleware groups** (`tpy.http.MiddlewareManager`).
- **Health & lifecycle** (`tpy.http`): `/health`, `/health/ready`, boot/shutdown/before/after/exception hooks.
- **Logging** (`tpy.logging`): channels (`console`, `file`, `stack`) via `LogManager` / `get_logger`.
- **Configuration** (`tpy.config.Config`): nested keys, env overlay, `cache` / `load_cached` / `load_auto`, freshness checks, `TPY_CONFIG_CACHE`.
- **Route cache** (`tpy.http.RouteCache`): `tpy route cache | list | clear`.
- **CLI DX**: `tpy -V` / `--version`, `tpy about`, `tpy commands`, Rich banners (`Console.banner` / `table` / `rule`).
- **Optimize & watch**: `tpy optimize` (config + route cache), `tpy watch` (rebuild on `schema.tpy` change).
- Optional extra: `tamilPY[redis]` (also included in `tamilPY[all]`).

### Added — documentation

- GitHub Pages client **study guides** : clickable feature cards → detail pages (`schema.html`, `api-response.html`, …).
- Shared responsive stylesheet (`docs/docs.css`): mobile hamburger nav, stacked footer link chips, touch-friendly targets.
- Schema grammar notes for `relations { }` (`docs/schema-grammar.md`).

### Changed

- Generated SQL repositories expose `query()`; `all()` / `find()` use the Query Builder (existing CRUD methods retained).
- `tpy new` scaffolds `app/schedule.py` and `storage/framework/cache/`.
- Kernel / Application load config via `Config.load_auto()`.
- Soft-break: `tpy.runtime.response.Response` and legacy validation helpers kept; prefer `ApiResponse` and `tpy.validation` for new code.

### CLI (new in 0.1.9)

```bash
tpy queue table | work
tpy schedule run | list
tpy cache clear
tpy config show | cache | status | clear
tpy route cache | list | clear
tpy optimize [--skip-routes]
tpy watch [--with-db] [--interval 1]
tpy about | commands | -V
```

### Upgrade

```bash
pip install --upgrade "tamilPY[all]"
# Redis drivers only:
pip install --upgrade "tamilPY[redis]"
```

After upgrading an existing app, regenerate repositories with `tpy build` / `tpy crud` to pick up `query()`. Add optional `relations { }` blocks in `schema.tpy` when ready. For faster production boots: `tpy optimize` then set `TPY_CONFIG_CACHE=1`.

---

## [0.1.8] - 2026-07-28

Security hardening, packaging cleanup, CI foundation, schema DSL expansions, and developer docs toward 1.0.

### Security
- JWT secret fails closed when missing or weak (no hardcoded fallback).
- Bootstrap admin password is randomized and written to `storage/auth_bootstrap.txt`.
- In-memory rate limiting / lockout guidance on generated `/auth/login`.

### Packaging
- `LICENSE` shipped in the distribution; `[project.urls]` added.
- Optional DB extras: `tamilPY[postgres]`, `[mysql]`, `[mongodb]`, `[all]` (SQLite needs no extra).
- `py.typed` marker for downstream type checkers.
- PyPI Trusted Publishing (OIDC) for releases.

### Developer experience
- Exception hierarchy (`TpyError` / `TpyParseError` / â€¦).
- Lazy imports for faster CLI startup.
- Providers usable as context managers.
- CI (pytest, Ruff, MyPy) on Python 3.12/3.13.
- Provider unit tests and CLI e2e health check.

### Schema DSL
- Composite unique constraints.
- Foreign-key `on_delete` / `on_update` options.
- Enum field type.

### Docs
- CONTRIBUTING, CODE_OF_CONDUCT, SECURITY.
- Schema grammar spec and SemVer / deprecation policy.
- Explicit async/sync trade-off for the generated DB layer.

### Upgrade
```bash
pip install --upgrade "tamilPY[all]"
# or install only the drivers you need:
pip install --upgrade "tamilPY[postgres]"
```

---

## [0.1.7] - 2026-07-27

Brings built-in authentication, MongoDB support, a secure admin experience, and developer productivity improvements.

### Added
- **MongoDB Support**: Native MongoDB integration with simple configuration and seamless connectivity.
- **Authentication (`tpy auth`)**: Generates a complete JWT authentication system with endpoints:
  - Register, Login, Refresh Token, Logout, Current User (`/me`)
  - Secure password hashing by default.
  - Server-side refresh token revocation.
  - Access and Refresh Token authentication flow.
- **Default User & Roles**: Default `User` and `AuthRole` schemas, auto-seeding:
  - Super Admin, Admin, Developer roles.
  - Bootstrap administrator account (`admin@example.com` / `admin123`).
- **Admin Dashboard**:
  - React-based Admin Login with Bearer token authentication.
  - Automatic token refresh on HTTP 401 responses.
  - Secure logout support.
  - Dashboard access restricted to Super Admin and Developer; Admin users are API-only.

### Changed
- `tpy migrate` now automatically generates missing database migrations, CRUD operations, and API scaffolding for newly created schema models.

### Security
- Password fields automatically excluded from API response schemas.
- Improved authentication and response serialization.

### Upgrade
```
pip install --upgrade tamilPY
```
---

## [0.1.6] - 2026-07-27

### Added
- **Admin UI Generator** (optional): scaffolds a Vite-based React admin interface.
  - New command: `tpy admin` to generate the admin interface.
  - New flag: `tpy build --with-ui` to include the Admin UI during project creation.
- Ready-to-use Vite-based frontend setup for fast development.
- Simplified project setup with minimal configuration.

### Usage
```
tpy admin
# or
tpy build --with-ui

cd admin
npm install
npm run dev
```
Dev server available at `http://127.0.0.1:5173/`.

---

## [0.1.5] - 2026-07-25

### Added
- **Foreign Key Relationships**: Support for defining relationships using the `references` keyword.
  ```
  user_id: uuid references User
  author: uuid references User.id
  ```
  - Defaults to referencing the target model's `id` column; custom target columns supported.
  - Generates SQL foreign key constraints automatically.
  - Ensures referenced models are migrated before dependent models.
- **Default Field Values**: Fields support default values via the `default` keyword (numbers, strings, booleans).
  ```
  stock: int default 0
  active: bool default true
  status: string default "draft"
  ```
  - Fields with defaults become optional in the generated Create API.

### Changed
- Improved schema parser for relation definitions.
- Enhanced migration generation for foreign key constraints.
- Better validation of default value expressions.
- Improved generated CRUD APIs for optional default fields.

### Compatibility
- Backward compatible with previous schema definitions; no breaking changes.
---

## [0.1.4] - 2026-07-24 â€” Initial Public Release ðŸŽ‰

First public release of **tamilPY** â€” a Python framework and CLI that accelerates backend API development through schema-driven code generation.

### Added
- Schema-driven application generation from a single `schema.tpy` file.
- Interactive database configuration wizard.
- FastAPI REST API generation.
- Automatic CRUD generation.
- Database migrations support.
- Sample data seeding.
- Multi-database support: SQLite, PostgreSQL, MySQL, MongoDB.
- Environment-based configuration.
- Project validation utilities (`tpy doctor`).
- CLI commands: `tpy new`, `tpy build`, `tpy build --skip-db`, `tpy crud`, `tpy db configure`, `tpy migrate`, `tpy migrate rollback`, `tpy seed`, `tpy serve`, `tpy doctor`, `tpy version`.

### Installation
```
pip install tamilPY
```
---
## [0.1.0 â€“ 0.1.3] - Initial Setup (Pre-release)

- Initial project scaffolding and internal setup phase.
- Core groundwork for schema-driven code generation laid out.
- No individual public GitHub releases were published for these versions; work culminated in the first public release, `0.1.4`.
