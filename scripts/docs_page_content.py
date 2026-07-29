"""
Study-material page bodies for tamilPY GitHub Pages.

Each page teaches: goals → why → setup → how it works → examples → API → mistakes.
"""

from __future__ import annotations

# Shared learning chrome helpers (HTML fragments)
GOALS_OPEN = '<div class="callout"><strong style="color:var(--ink);">What you will learn</strong><ul style="margin:0.6rem 0 0;">'
GOALS_CLOSE = "</ul></div>"


def goals(*items: str) -> str:
    lis = "".join(f"<li>{item}</li>" for item in items)
    return f"{GOALS_OPEN}{lis}{GOALS_CLOSE}"


PAGES: list[dict] = [
    {
        "file": "schema.html",
        "tag": "Feature 01 · Study guide",
        "title": "Schema-first generation",
        "lead": "Learn how one schema.tpy file becomes a full FastAPI stack — and how to run that workflow yourself.",
        "prev": None,
        "next": ("database.html", "Multi-database"),
        "body": f"""
{goals(
    "What schema-first means in tamilPY",
    "How to write schema.tpy and regenerate safely",
    "Which files are created and what each layer does",
)}

<h2>1. Why schema-first?</h2>
<p>In a normal FastAPI project you write models, Pydantic schemas, SQL, repositories, services, controllers, and routes by hand — for every entity. tamilPY flips that: you describe the domain once in <code>schema.tpy</code>, then generators produce a consistent layered app.</p>
<p>That gives clients a predictable project shape, faster MVPs, and fewer copy-paste bugs.</p>

<h2>2. Setup (first time)</h2>
<ol>
  <li>Install: <code>pip install tamilPY</code> (Python 3.12+).</li>
  <li>Scaffold: <code>tpy new myapp</code> then <code>cd myapp</code>.</li>
  <li>Open <code>schema.tpy</code> and define your models.</li>
  <li>Run <code>tpy build</code> (DB wizard + generate) or <code>tpy build --skip-db</code> if <code>.env</code> already exists.</li>
  <li>Apply DB: <code>tpy migrate</code>, optionally <code>tpy seed</code>.</li>
  <li>Serve: <code>tpy serve</code> and open <code>/docs</code>.</li>
</ol>

<pre><span class="prompt">$</span> pip install tamilPY
<span class="prompt">$</span> tpy new myapp &amp;&amp; cd myapp
<span class="prompt">$</span> # edit schema.tpy
<span class="prompt">$</span> tpy build
<span class="prompt">$</span> tpy migrate &amp;&amp; tpy seed
<span class="prompt">$</span> tpy serve</pre>

<h2>3. How generation works</h2>
<p>When you run <code>tpy build</code> / <code>tpy crud</code>:</p>
<ol>
  <li>The parser reads <code>schema.tpy</code> into an AST (models, fields, relations).</li>
  <li>Generators fill Jinja templates with that context.</li>
  <li>Files are written under <code>app/</code> and <code>database/migrations/</code>.</li>
  <li>Routers are wired so FastAPI exposes REST endpoints.</li>
</ol>

<div class="callout">You edit the <strong style="color:var(--ink);">schema</strong> as the source of truth. Regenerating refreshes generated layers from that schema.</div>

<h2>4. Write a real schema</h2>
<pre>database sqlite

model User {{
  id: uuid primary
  name: string required
  email: string unique required
  age: int nullable
}}

model Post {{
  id: uuid primary
  title: string required index
  body: string nullable
  user_id: uuid references User on_delete cascade
  published: bool default false
  relations {{
    belongs_to User as author via user_id
  }}
}}</pre>

<h2>5. What gets generated</h2>
<table class="doc-table">
  <thead><tr><th>Layer</th><th>Path</th><th>Responsibility</th></tr></thead>
  <tbody>
    <tr><td>Model</td><td><code>app/models/</code></td><td>Field shape</td></tr>
    <tr><td>Migration</td><td><code>database/migrations/</code></td><td>Create/alter tables</td></tr>
    <tr><td>Schema</td><td><code>app/schemas/</code></td><td>Create / Update / Response DTOs</td></tr>
    <tr><td>Repository</td><td><code>app/repositories/</code></td><td>DB access + <code>query()</code></td></tr>
    <tr><td>Service</td><td><code>app/services/</code></td><td>Business use-cases</td></tr>
    <tr><td>Controller</td><td><code>app/controllers/</code></td><td>HTTP → service</td></tr>
    <tr><td>Route</td><td><code>app/routes/</code></td><td>FastAPI router</td></tr>
  </tbody>
</table>

<h2>6. After you change the schema</h2>
<ol>
  <li>Save <code>schema.tpy</code>.</li>
  <li>Run <code>tpy crud</code> (or <code>tpy watch</code> in another terminal).</li>
  <li>Run <code>tpy migrate</code> if tables/columns changed.</li>
  <li>Restart or rely on <code>tpy serve --reload</code>.</li>
</ol>

<h2>7. Common mistakes</h2>
<ul>
  <li>Editing only generated files and expecting them to survive the next <code>tpy crud</code> — put durable logic in services carefully.</li>
  <li>Referencing a model that is defined later — put parents first so migrations order correctly.</li>
  <li>Forgetting <code>tpy migrate</code> after adding fields.</li>
</ul>
""",
    },
    {
        "file": "database.html",
        "tag": "Feature 02 · Study guide",
        "title": "Multi-database",
        "lead": "Choose SQLite, PostgreSQL, MySQL, or MongoDB — and learn how tamilPY stores and uses that choice.",
        "prev": ("schema.html", "Schema-first generation"),
        "next": ("migrate.html", "Auto database create"),
        "body": f"""
{goals(
    "Which databases tamilPY supports",
    "How the build wizard writes .env and schema",
    "How to switch providers later with tpy db configure",
)}

<h2>1. Supported providers</h2>
<table class="doc-table">
  <thead><tr><th>Provider</th><th>Best for</th><th>Notes</th></tr></thead>
  <tbody>
    <tr><td><code>sqlite</code></td><td>Learning / local demos</td><td>No server; file-based</td></tr>
    <tr><td><code>postgres</code></td><td>Production SQL</td><td>Full FK / indexes</td></tr>
    <tr><td><code>mysql</code></td><td>Production SQL</td><td>Same CRUD path</td></tr>
    <tr><td><code>mongodb</code></td><td>Documents</td><td>Collections + indexes; refs are metadata</td></tr>
  </tbody>
</table>

<h2>2. Setup during build</h2>
<pre><span class="prompt">$</span> tpy build</pre>
<p>The wizard asks for provider, host, port, user, and password. It writes:</p>
<ul>
  <li><code>.env</code> — connection URL / credentials</li>
  <li><code>tpy.toml</code> — app settings</li>
  <li><code>schema.tpy</code> — optional <code>database …</code> line</li>
</ul>

<pre><span class="prompt">$</span> pip install "tamilPY[all]"   <span style="color:var(--muted)"># SQL + Mongo drivers</span>
<span class="prompt">$</span> pip install "tamilPY[redis]" <span style="color:var(--muted)"># Redis cache/queue</span></pre>

<h2>3. Reconfigure later</h2>
<pre><span class="prompt">$</span> tpy db configure
<span class="prompt">$</span> tpy db info
<span class="prompt">$</span> tpy db ping</pre>
<p><code>info</code> prints the active provider and URL shape. <code>ping</code> opens a real connection so you know credentials work before migrate.</p>

<h2>4. How the runtime uses it</h2>
<p>Providers are selected from config. Generated repositories call the active provider for SQL/Mongo operations. You usually do not import drivers yourself inside controllers.</p>

<h2>5. Common mistakes</h2>
<ul>
  <li>Installing the framework without DB extras, then wondering why Postgres fails to import.</li>
  <li>Changing only <code>schema.tpy</code> database line without updating <code>.env</code>.</li>
</ul>
""",
    },
    {
        "file": "migrate.html",
        "tag": "Feature 03 · Study guide",
        "title": "Auto database create",
        "lead": "Understand migrate: create missing SQL databases, apply ordered migrations, roll back safely.",
        "prev": ("database.html", "Multi-database"),
        "next": ("crud-api.html", "Full CRUD REST API"),
        "body": f"""
{goals(
    "What tpy migrate does step by step",
    "How migration files are ordered",
    "When to use status and rollback",
)}

<h2>1. Setup</h2>
<p>You need a project with generated migrations and a valid <code>.env</code> (from <code>tpy build</code> or <code>tpy db configure</code>).</p>

<pre><span class="prompt">$</span> tpy migrate
<span class="prompt">$</span> tpy migrate status
<span class="prompt">$</span> tpy migrate rollback</pre>

<h2>2. How it works</h2>
<ol>
  <li>Load database settings from the environment.</li>
  <li>For Postgres/MySQL: if the database name is missing, attempt to create it.</li>
  <li>Connect to the target database.</li>
  <li>Apply pending files in <code>database/migrations/</code> in numeric order (<code>001_</code>, <code>002_</code>, …).</li>
  <li>Record applied migrations so the next run only applies new ones.</li>
</ol>

<h2>3. Migration files</h2>
<pre>database/migrations/
  001_user_migration.py
  002_post_migration.py</pre>
<p>Each file provides <code>up</code> (apply) and <code>down</code> (undo). Model order in <code>schema.tpy</code> becomes migration order — define referenced models first.</p>

<h2>4. After schema changes</h2>
<ol>
  <li><code>tpy crud</code> — regenerate migration + layers.</li>
  <li><code>tpy migrate</code> — apply new pending files.</li>
  <li><code>tpy migrate status</code> — confirm what ran.</li>
</ol>

<div class="callout">SQLite creates the file database automatically on connect. Auto-create of a named server DB is mainly for Postgres/MySQL.</div>

<h2>5. Common mistakes</h2>
<ul>
  <li>Running migrate before <code>tpy build</code>/<code>tpy crud</code> (no migration files yet).</li>
  <li>Hand-editing applied migrations instead of adding a new ordered file.</li>
</ul>
""",
    },
    {
        "file": "crud-api.html",
        "tag": "Feature 04 · Study guide",
        "title": "Full CRUD REST API",
        "lead": "See the exact endpoints tamilPY generates and how to call them from Swagger or HTTP clients.",
        "prev": ("migrate.html", "Auto database create"),
        "next": ("layers.html", "Layered architecture"),
        "body": f"""
{goals(
    "Default REST routes for each model",
    "How to try them in /docs",
    "Where to customize responses",
)}

<h2>1. Setup</h2>
<pre><span class="prompt">$</span> tpy build &amp;&amp; tpy migrate
<span class="prompt">$</span> tpy serve
<span class="prompt">#</span> open http://127.0.0.1:8000/docs</pre>

<h2>2. How routes are named</h2>
<p>Model <code>User</code> becomes plural prefix <code>/users</code>:</p>
<table class="doc-table">
  <thead><tr><th>Method</th><th>Path</th><th>Meaning</th></tr></thead>
  <tbody>
    <tr><td><code>GET</code></td><td><code>/users/</code></td><td>List records</td></tr>
    <tr><td><code>GET</code></td><td><code>/users/{{id}}</code></td><td>Fetch one</td></tr>
    <tr><td><code>POST</code></td><td><code>/users/</code></td><td>Create</td></tr>
    <tr><td><code>PUT</code></td><td><code>/users/{{id}}</code></td><td>Update</td></tr>
    <tr><td><code>DELETE</code></td><td><code>/users/{{id}}</code></td><td>Delete</td></tr>
  </tbody>
</table>

<h2>3. Request flow</h2>
<ol>
  <li>HTTP hits the generated FastAPI route.</li>
  <li>Controller validates/parses the body (Pydantic schema).</li>
  <li>Service runs the use-case.</li>
  <li>Repository talks to the database.</li>
  <li>JSON returns to the client.</li>
</ol>

<h2>4. Example create</h2>
<pre>POST /users/
Content-Type: application/json

{{
  "name": "Asha",
  "email": "asha@example.com"
}}</pre>

<p>Prefer wrapping controller returns with <a href="api-response.html" style="color:var(--amber);">ApiResponse</a> when you customize handlers so every client sees the same envelope.</p>

<h2>5. Common mistakes</h2>
<ul>
  <li>Calling <code>/user</code> instead of <code>/users</code> (pluralization).</li>
  <li>Forgetting required fields from the schema (<code>required</code> / non-nullable).</li>
</ul>
""",
    },
    {
        "file": "layers.html",
        "tag": "Feature 05 · Study guide",
        "title": "Layered architecture",
        "lead": "Learn the Repository → Service → Controller → Route stack so you know where to put new code.",
        "prev": ("crud-api.html", "Full CRUD REST API"),
        "next": ("workflow.html", "Migrate · seed · serve"),
        "body": f"""
{goals(
    "What each layer owns",
    "Where to add custom business rules",
    "How regeneration interacts with your edits",
)}

<h2>1. The stack</h2>
<div class="flow">
  <div class="flow-item"><div class="flow-step"><span class="n">01</span>REPO</div><div><h3>Repository</h3><p>Only database concerns: SQL/Mongo, <code>query()</code>, CRUD helpers. No HTTP.</p></div></div>
  <div class="flow-item"><div class="flow-step"><span class="n">02</span>SERVICE</div><div><h3>Service</h3><p>Use-cases: validation orchestration, events, multi-repo workflows.</p></div></div>
  <div class="flow-item"><div class="flow-step"><span class="n">03</span>CTRL</div><div><h3>Controller</h3><p>Translate HTTP ↔ service. Return <code>ApiResponse</code>.</p></div></div>
  <div class="flow-item"><div class="flow-step"><span class="n">04</span>ROUTE</div><div><h3>Route</h3><p>Register paths on FastAPI; keep handlers thin.</p></div></div>
</div>

<h2>2. Setup / finding files</h2>
<p>After generate, look under:</p>
<pre>app/repositories/
app/services/
app/controllers/
app/routes/</pre>

<h2>3. Where should my code go?</h2>
<table class="doc-table">
  <thead><tr><th>Change</th><th>Put it in</th></tr></thead>
  <tbody>
    <tr><td>New SQL filter / join</td><td>Repository / Query Builder</td></tr>
    <tr><td>“When order placed, send email”</td><td>Service + Events/Queue</td></tr>
    <tr><td>Status code / JSON envelope</td><td>Controller + ApiResponse</td></tr>
    <tr><td>URL path / method</td><td>Route</td></tr>
  </tbody>
</table>

<h2>4. Regeneration tip</h2>
<p><code>tpy crud</code> may overwrite generated files. Keep a plan: either re-apply patches, protect customized modules, or extend via services that you own.</p>
""",
    },
    {
        "file": "workflow.html",
        "tag": "Feature 06 · Study guide",
        "title": "Migrate · seed · serve",
        "lead": "The everyday developer loop: apply schema, load sample data, run the API.",
        "prev": ("layers.html", "Layered architecture"),
        "next": ("logging-health.html", "Logging & health"),
        "body": f"""
{goals(
    "The migrate → seed → serve loop",
    "What each command changes on disk / DB",
    "How to combine with watch + reload",
)}

<h2>1. Setup</h2>
<p>Project must already exist (<code>tpy new</code> + <code>tpy build</code>).</p>

<pre><span class="prompt">$</span> tpy migrate
<span class="prompt">$</span> tpy seed
<span class="prompt">$</span> tpy serve</pre>

<h2>2. What each step does</h2>
<ul>
  <li><strong style="color:var(--ink);">migrate</strong> — create DB if needed; apply pending migrations.</li>
  <li><strong style="color:var(--ink);">seed</strong> — run Python seeders in <code>database/seeds/</code> (demo users, roles, sample rows).</li>
  <li><strong style="color:var(--ink);">serve</strong> — start uvicorn on <code>app.main:app</code> (reload on by default).</li>
</ul>

<h2>3. Recommended local DX</h2>
<pre><span class="prompt">#</span> terminal 1
<span class="prompt">$</span> tpy serve --reload

<span class="prompt">#</span> terminal 2
<span class="prompt">$</span> tpy watch</pre>
<p>Watch rebuilds layers when <code>schema.tpy</code> changes; serve reloads Python. After structural DB changes, still run <code>tpy migrate</code>.</p>

<h2>4. Common mistakes</h2>
<ul>
  <li>Seeding before migrate (tables missing).</li>
  <li>Expecting seed to be idempotent without writing seeds that way.</li>
</ul>
""",
    },
    {
        "file": "logging-health.html",
        "tag": "Feature 07 · Study guide",
        "title": "Logging &amp; health",
        "lead": "Wire logs clients can trust, and expose health endpoints for probes.",
        "prev": ("workflow.html", "Migrate · seed · serve"),
        "next": ("admin.html", "React admin dashboard"),
        "body": f"""
{goals(
    "How to write application logs",
    "Where log files live",
    "What /health and /health/ready mean",
)}

<h2>1. Setup logging</h2>
<pre>from tpy.logging import get_logger

log = get_logger("app")
log.info("server started", host="127.0.0.1")
log.error("payment failed", order_id="ord_1")</pre>

<p>By default you get console output and a file under <code>storage/logs/</code>. Channels: <code>console</code>, <code>file</code>, <code>stack</code>.</p>

<pre>from tpy.logging import LogManager

manager = LogManager()
manager.configure(level="DEBUG", log_dir="storage/logs", app_name="myapp")
manager.channel("file").warning("only file")</pre>

<h2>2. Health endpoints</h2>
<table class="doc-table">
  <thead><tr><th>Path</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>GET /health</code></td><td>Process is up (liveness)</td></tr>
    <tr><td><code>GET /health/ready</code></td><td>Ready to take traffic (when Application mounts checks)</td></tr>
  </tbody>
</table>

<p>Use these in Docker/Kubernetes probes or load balancer checks.</p>

<h2>3. How it connects to the kernel</h2>
<p>If you boot with <code>Application(...).create()</code> / <code>mount()</code>, logging and health helpers register with the app. Generated <code>app/main.py</code> still exposes a basic health route for soft-break projects.</p>

<p>More depth: <a href="logging-config.html" style="color:var(--amber);">Logging &amp; Config</a>.</p>
""",
    },
    {
        "file": "admin.html",
        "tag": "Feature 08 · Study guide",
        "title": "React admin dashboard",
        "lead": "Generate and run a Vite + React admin UI that matches your schema models.",
        "prev": ("logging-health.html", "Logging & health"),
        "next": ("auth.html", "JWT auth"),
        "body": f"""
{goals(
    "How to generate the admin app",
    "How the UI discovers models",
    "How to refresh after schema changes",
)}

<h2>1. Setup</h2>
<pre><span class="prompt">$</span> tpy serve          <span style="color:var(--muted)"># API on :8000</span>
<span class="prompt">$</span> tpy admin          <span style="color:var(--muted)"># writes admin/</span>
<span class="prompt">$</span> cd admin
<span class="prompt">$</span> npm install
<span class="prompt">$</span> npm run dev        <span style="color:var(--muted)"># UI on :5173</span></pre>
<p>The wizard asks for the API base URL (default <code>http://127.0.0.1:8000</code>).</p>

<h2>2. How it works</h2>
<ol>
  <li><code>tpy admin</code> reads <code>schema.tpy</code>.</li>
  <li>It generates <code>admin/src/data/models.js</code> (model registry).</li>
  <li>Shared pages (list + form) render every model using that registry.</li>
  <li>The UI calls your generated CRUD REST endpoints.</li>
</ol>

<h2>3. Important paths</h2>
<table class="doc-table">
  <thead><tr><th>Path</th><th>Role</th></tr></thead>
  <tbody>
    <tr><td><code>admin/src/data/models.js</code></td><td>Schema-driven registry</td></tr>
    <tr><td><code>admin/src/components/</code></td><td>Layout, DataTable, RecordForm</td></tr>
    <tr><td><code>admin/src/pages/</code></td><td>Generic list/form pages</td></tr>
  </tbody>
</table>

<h2>4. After schema changes</h2>
<pre><span class="prompt">$</span> tpy crud
<span class="prompt">$</span> tpy admin   <span style="color:var(--muted)"># refresh UI registry</span>
<span class="prompt">$</span> tpy migrate</pre>

<div class="callout">With <code>tpy auth</code>, only <strong style="color:var(--ink);">super-admin</strong> and <strong style="color:var(--ink);">developer</strong> roles can use the dashboard login gate.</div>
""",
    },
    {
        "file": "auth.html",
        "tag": "Feature 09 · Study guide",
        "title": "JWT authentication",
        "lead": "Enable AuthRole + User, issue access/refresh tokens, and protect the admin UI.",
        "prev": ("admin.html", "React admin dashboard"),
        "next": ("doctor.html", "Doctor & DB tools"),
        "body": f"""
{goals(
    "How to enable auth in an existing project",
    "Which endpoints are created",
    "How roles affect the admin dashboard",
)}

<h2>1. Setup</h2>
<pre><span class="prompt">$</span> tpy auth
<span class="prompt">$</span> pip install -r requirements.txt
<span class="prompt">$</span> tpy migrate &amp;&amp; tpy seed
<span class="prompt">$</span> tpy serve</pre>
<p>Default seeded login: <code>admin@example.com</code> / <code>admin123</code> (super-admin).</p>

<h2>2. What gets added</h2>
<ul>
  <li>Schema models: <code>AuthRole</code>, <code>User</code> (password hashed).</li>
  <li>Auth routes under <code>/auth/*</code>.</li>
  <li>JWT access token (short-lived) + refresh token (longer-lived).</li>
  <li>Logout revokes refresh server-side.</li>
</ul>

<h2>3. API map</h2>
<table class="doc-table">
  <thead><tr><th>Endpoint</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>POST /auth/register</code></td><td>Create user</td></tr>
    <tr><td><code>POST /auth/login</code></td><td>Return access + refresh</td></tr>
    <tr><td><code>POST /auth/refresh</code></td><td>Rotate access using refresh</td></tr>
    <tr><td><code>POST /auth/logout</code></td><td>Revoke refresh</td></tr>
    <tr><td><code>GET /auth/me</code></td><td>Current user profile</td></tr>
  </tbody>
</table>

<h2>4. How a client uses tokens</h2>
<ol>
  <li>Login → store access + refresh securely.</li>
  <li>Send <code>Authorization: Bearer &lt;access&gt;</code> on protected routes.</li>
  <li>On 401, call refresh; if refresh fails, force login again.</li>
</ol>

<h2>5. Roles</h2>
<p>Dashboard access: <strong style="color:var(--ink);">super-admin</strong> and <strong style="color:var(--ink);">developer</strong>. The <code>admin</code> role is API-oriented by default.</p>
""",
    },
    {
        "file": "doctor.html",
        "tag": "Feature 10 · Study guide",
        "title": "Doctor &amp; DB tools",
        "lead": "Diagnose project structure and database connectivity before you debug application code.",
        "prev": ("auth.html", "JWT auth"),
        "next": ("query.html", "Query & relations"),
        "body": f"""
{goals(
    "When to run tpy doctor",
    "How db info / ping help connection issues",
    "What tpy about shows",
)}

<h2>1. Setup</h2>
<p>Run these inside a tamilPY project root (where <code>schema.tpy</code> lives).</p>

<pre><span class="prompt">$</span> tpy doctor
<span class="prompt">$</span> tpy db info
<span class="prompt">$</span> tpy db ping
<span class="prompt">$</span> tpy about
<span class="prompt">$</span> tpy commands</pre>

<h2>2. How to use them</h2>
<ul>
  <li><code>doctor</code> — missing folders/files after a bad copy or partial generate.</li>
  <li><code>db info</code> — confirms which driver/URL the CLI thinks you configured.</li>
  <li><code>db ping</code> — proves the network/credentials work.</li>
  <li><code>about</code> — framework version, Python, whether this folder is a TPY project, cache status.</li>
</ul>

<div class="callout">If migrate fails, run <code>tpy db ping</code> first. Many “framework bugs” are wrong host/password.</div>
""",
    },
    {
        "file": "query.html",
        "tag": "Platform 01–02 · Study guide",
        "title": "Query Builder &amp; relations",
        "lead": "Build safe, fluent database queries and load relationships without N+1 loops.",
        "prev": ("doctor.html", "Doctor & DB tools"),
        "next": ("events.html", "Events & listeners"),
        "body": f"""
{goals(
    "How to get a query from a repository",
    "Common filters, ordering, pagination",
    "How schema relations + with_() work together",
)}

<h2>1. Setup</h2>
<p>Generate repositories with <code>tpy build</code> / <code>tpy crud</code> so each repo exposes <code>query()</code>. No extra install beyond your database driver.</p>

<pre>from app.repositories.user_repository import UserRepository

repo = UserRepository()
rows = repo.query().where("email", "asha@example.com").get()
one = repo.query().find(user_id)</pre>

<h2>2. How the Query Builder works</h2>
<ol>
  <li><code>repo.query()</code> returns a fluent builder bound to the model table.</li>
  <li>You chain filters (<code>where</code>), sorts (<code>order_by</code>), limits, etc.</li>
  <li>Terminal methods (<code>get</code>, <code>first</code>, <code>find</code>, <code>paginate</code>) execute parameterized SQL (or Mongo helpers).</li>
</ol>

<pre>page = (
    repo.query()
    .where("published", True)
    .order_by("created_at", "desc")
    .paginate(page=1, per_page=20)
)</pre>

<h2>3. Relations in schema.tpy</h2>
<pre>model Post {{
  id: uuid primary
  user_id: uuid references User on_delete cascade
  title: string required
  relations {{
    belongs_to User as author via user_id
  }}
}}

model User {{
  id: uuid primary
  email: string unique required
  relations {{
    has_many Post as posts
  }}
}}</pre>

<table class="doc-table">
  <thead><tr><th>Kind</th><th>Meaning</th></tr></thead>
  <tbody>
    <tr><td><code>belongs_to</code></td><td>This row stores the foreign key</td></tr>
    <tr><td><code>has_many</code> / <code>has_one</code></td><td>Related rows point back</td></tr>
    <tr><td><code>belongs_to_many</code></td><td>Many-to-many through a pivot model</td></tr>
  </tbody>
</table>

<h2>4. Eager loading</h2>
<pre>posts = repo.query().with_("author").get()
# Avoids N+1: loads authors in a follow-up query, then attaches them</pre>

<h2>5. Common mistakes</h2>
<ul>
  <li>String-concatenating SQL instead of using the builder (injection risk).</li>
  <li>Calling related attributes in a loop without <code>with_()</code>.</li>
</ul>
""",
    },
    {
        "file": "events.html",
        "tag": "Platform 03 · Study guide",
        "title": "Events &amp; listeners",
        "lead": "Decouple side effects (emails, audits, cache busts) from core request code using a sync event bus.",
        "prev": ("query.html", "Query & relations"),
        "next": ("queue.html", "Background jobs"),
        "body": f"""
{goals(
    "How to define an Event and Listener",
    "How dispatch order and stop() work",
    "When to use events vs queue jobs",
)}

<h2>1. Setup</h2>
<p>No extra package. Import from <code>tpy.events</code> anywhere (service layer is typical).</p>

<pre>from tpy.events import Event, Listener, EventDispatcher

class OrderPlaced(Event):
    def __init__(self, order_id: str) -> None:
        super().__init__()
        self.order_id = order_id

class LogOrder(Listener):
    def handle(self, event: Event) -> None:
        assert isinstance(event, OrderPlaced)
        print("order", event.order_id)

bus = EventDispatcher()
bus.listen(OrderPlaced, LogOrder())
bus.listen(OrderPlaced, lambda e: print("also", e.order_id))
bus.dispatch(OrderPlaced("ord_1"))</pre>

<h2>2. How it works</h2>
<ol>
  <li>You create a typed <code>Event</code> subclass carrying payload fields.</li>
  <li>Listeners register with <code>listen(EventType, listener)</code>.</li>
  <li><code>dispatch</code> runs typed listeners in order, then wildcard <code>"*"</code> listeners.</li>
  <li>Call <code>event.stop()</code> inside a listener to halt remaining typed listeners.</li>
  <li>Exceptions fail-fast (they propagate to the caller).</li>
</ol>

<table class="doc-table">
  <thead><tr><th>API</th><th>Use when</th></tr></thead>
  <tbody>
    <tr><td><code>listen</code></td><td>Register class or callable</td></tr>
    <tr><td><code>dispatch</code></td><td>Notify all listeners</td></tr>
    <tr><td><code>dispatch_until</code></td><td>Stop at first non-None return</td></tr>
    <tr><td><code>forget</code></td><td>Clear listeners for a type</td></tr>
  </tbody>
</table>

<div class="callout">Events are <strong style="color:var(--ink);">synchronous</strong>. For slow work (email SMTP, webhooks), dispatch an event that <em>enqueues a Job</em> — see the Queue guide.</div>
""",
    },
    {
        "file": "queue.html",
        "tag": "Platform 04 · Study guide",
        "title": "Background jobs",
        "lead": "Move slow work off the request thread with sync, database, or Redis queue drivers.",
        "prev": ("events.html", "Events & listeners"),
        "next": ("schedule.html", "Task scheduler"),
        "body": f"""
{goals(
    "How to define a Job class",
    "How to push work and run a worker",
    "Which driver to pick (sync / database / redis)",
)}

<h2>1. Setup</h2>
<pre>from tpy.queue import Job, Queue, SyncQueueDriver

class SendWelcomeEmail(Job):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

    def handle(self) -> None:
        # send email here
        print("welcome", self.user_id)

# Development: run inline in the same process
Queue(SyncQueueDriver()).push(SendWelcomeEmail("u1"))</pre>

<h2>2. Database driver (typical local/prod without Redis)</h2>
<pre><span class="prompt">$</span> tpy queue table
<span class="prompt">$</span> tpy queue work --driver database --once
<span class="prompt">$</span> tpy queue work --driver database</pre>
<p><code>queue table</code> creates <code>_tpy_jobs</code> (and failed-job storage). Workers pull jobs and call <code>handle()</code>.</p>

<h2>3. Redis driver</h2>
<pre><span class="prompt">$</span> pip install "tamilPY[redis]"
<span class="prompt">$</span> tpy queue work --driver redis --redis-url redis://localhost:6379/0</pre>

<h2>4. How it works</h2>
<ol>
  <li>Your app code <code>push()</code>es a Job instance onto a Queue.</li>
  <li>The driver serializes and stores it (memory/inline, SQL table, or Redis list).</li>
  <li>A worker process pops jobs and executes <code>handle()</code>.</li>
  <li>Failures can land in a failed-jobs store depending on driver.</li>
</ol>

<div class="callout">Use <code>SyncQueueDriver</code> in tests. Use database/redis workers in real deployments so HTTP requests stay fast.</div>
""",
    },
    {
        "file": "schedule.html",
        "tag": "Platform 05 · Study guide",
        "title": "Task scheduler",
        "lead": "Register recurring tasks in app/schedule.py and run due work from cron or a supervisor.",
        "prev": ("queue.html", "Background jobs"),
        "next": ("cache.html", "Cache manager"),
        "body": f"""
{goals(
    "Where to register schedule entries",
    "How to list and run due tasks",
    "How to wire OS cron to tpy schedule run",
)}

<h2>1. Setup</h2>
<p><code>tpy new</code> scaffolds <code>app/schedule.py</code>. Edit <code>register()</code>:</p>

<pre># app/schedule.py
def register(schedule):
    schedule.command("cache:clear").daily()
    schedule.call(lambda: print("heartbeat")).every_minute()</pre>

<pre><span class="prompt">$</span> tpy schedule list
<span class="prompt">$</span> tpy schedule run</pre>

<h2>2. How it works</h2>
<ol>
  <li>CLI loads <code>app.schedule.register</code>.</li>
  <li>Each event has a cadence (every minute, hourly, daily, cron expression helpers).</li>
  <li><code>tpy schedule run</code> executes only tasks that are due now.</li>
  <li>Overlap locks prevent stacking the same task if a previous run is still active.</li>
</ol>

<h2>3. Production wiring</h2>
<pre><span class="prompt">#</span> cron example — every minute
* * * * * cd /var/www/myapp &amp;&amp; tpy schedule run</pre>

<p>Combine with queue workers: schedule can enqueue Jobs instead of doing heavy work inline.</p>
""",
    },
    {
        "file": "cache.html",
        "tag": "Platform 06 · Study guide",
        "title": "Cache manager",
        "lead": "Store temporary values in memory, on disk, or Redis — and clear them from the CLI.",
        "prev": ("schedule.html", "Task scheduler"),
        "next": ("api-response.html", "ApiResponse helpers"),
        "body": f"""
{goals(
    "How to construct a Cache with a store",
    "put / get / forget / remember patterns",
    "When to use memory vs file vs Redis",
)}

<h2>1. Setup</h2>
<pre>from tpy.cache import Cache, MemoryStore, FileStore

# Process memory (fast, lost on restart)
cache = Cache(MemoryStore())

# Shared file cache for local multi-process demos
cache = Cache(FileStore("storage/framework/cache"))

cache.put("user:1", {{"name": "Asha"}}, ttl=60)
user = cache.get("user:1")
cache.forget("user:1")</pre>

<pre><span class="prompt">$</span> tpy cache clear</pre>

<h2>2. Redis</h2>
<pre><span class="prompt">$</span> pip install "tamilPY[redis]"</pre>
<pre>from tpy.cache import Cache, RedisStore
cache = Cache(RedisStore(url="redis://localhost:6379/0"))</pre>

<h2>3. How it works</h2>
<ol>
  <li><code>Cache</code> is a small facade over a <code>CacheStore</code>.</li>
  <li><code>put</code> writes a value with optional TTL seconds.</li>
  <li><code>get</code> returns the value or a default if missing/expired.</li>
  <li>CLI <code>tpy cache clear</code> flushes the configured/default stores used by the project.</li>
</ol>

<table class="doc-table">
  <thead><tr><th>Store</th><th>Use when</th></tr></thead>
  <tbody>
    <tr><td>Memory</td><td>Single process, tests, tiny TTL data</td></tr>
    <tr><td>File</td><td>Local persistence without Redis</td></tr>
    <tr><td>Redis</td><td>Multi-server production cache</td></tr>
  </tbody>
</table>
""",
    },
    {
        "file": "api-response.html",
        "tag": "Platform 07 · Study guide",
        "title": "ApiResponse helpers",
        "lead": "Return one consistent JSON envelope from every controller so frontend and mobile clients stay simple.",
        "prev": ("cache.html", "Cache manager"),
        "next": ("validation.html", "Validation engine"),
        "body": f"""
{goals(
    "What the success/error JSON envelope looks like",
    "How to return ApiResponse from a FastAPI controller",
    "How pagination and validation errors map into that envelope",
)}

<h2>1. Why ApiResponse exists</h2>
<p>Without a shared helper, every controller invents its own JSON shape (<code>{{"ok": true}}</code>, <code>{{"data": ...}}</code>, bare lists, …). Clients then need special cases.</p>
<p><code>tpy.http.ApiResponse</code> always returns a FastAPI <code>JSONResponse</code> with a fixed envelope:</p>

<table class="doc-table">
  <thead><tr><th>Field</th><th>Success</th><th>Error</th></tr></thead>
  <tbody>
    <tr><td><code>success</code></td><td><code>true</code></td><td><code>false</code></td></tr>
    <tr><td><code>message</code></td><td>optional text</td><td>error summary</td></tr>
    <tr><td><code>data</code></td><td>payload</td><td>usually <code>null</code></td></tr>
    <tr><td><code>meta</code></td><td>pagination / extras</td><td>—</td></tr>
    <tr><td><code>errors</code></td><td>—</td><td>field map or list</td></tr>
  </tbody>
</table>

<h2>2. Setup (no extra install)</h2>
<p>If tamilPY is installed, import it in any controller:</p>
<pre>from tpy.http import ApiResponse</pre>
<p>Generated projects already depend on FastAPI, which <code>ApiResponse</code> uses for <code>JSONResponse</code>.</p>

<div class="callout">Soft-break: older <code>tpy.runtime.response.Response</code> still exists. Prefer <code>ApiResponse</code> for new FastAPI controllers.</div>

<h2>3. How it works (internally)</h2>
<ol>
  <li>Helpers call <code>ApiResponse.payload(...)</code> to build a plain <code>dict</code>.</li>
  <li>That dict is wrapped in FastAPI <code>JSONResponse</code> with an HTTP status code.</li>
  <li>Your route <code>return</code>s that response — FastAPI sends JSON to the client.</li>
</ol>

<h2>4. Success responses</h2>
<pre>from tpy.http import ApiResponse

# 200 OK
return ApiResponse.success(
    {{"id": "u1", "email": "asha@example.com"}},
    message="User loaded",
)

# 201 Created
return ApiResponse.created(
    {{"id": "u1"}},
    message="User created",
)</pre>

<p>Example JSON body for success:</p>
<pre>{{
  "success": true,
  "message": "User loaded",
  "data": {{"id": "u1", "email": "asha@example.com"}},
  "meta": null
}}</pre>

<h2>5. Use inside a controller</h2>
<pre>from fastapi import APIRouter
from tpy.http import ApiResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{{user_id}}")
def show_user(user_id: str):
    user = service.find(user_id)
    if not user:
        return ApiResponse.not_found("User not found")
    return ApiResponse.success(user, message="OK")

@router.post("/")
def create_user(payload: UserCreate):
    row = service.create(payload.model_dump())
    return ApiResponse.created(row)</pre>

<h2>6. Pagination</h2>
<p><code>paginated()</code> accepts a Query Builder paginator (<code>to_dict()</code>) or a dict with <code>data</code> + <code>meta</code>:</p>
<pre>page = repo.query().paginate(page=1, per_page=20)
return ApiResponse.paginated(page, message="Users page")</pre>
<pre>{{
  "success": true,
  "message": "Users page",
  "data": [ /* rows */ ],
  "meta": {{
    "current_page": 1,
    "per_page": 20,
    "total": 105
    /* …paginator fields */
  }}
}}</pre>

<h2>7. Errors</h2>
<pre># Generic error (default 400)
return ApiResponse.error("Email already used", status_code=409)

# Shortcuts
return ApiResponse.not_found()      # 404
return ApiResponse.unauthorized()   # 401
return ApiResponse.forbidden()      # 403
return ApiResponse.no_content()     # 204 empty body</pre>

<p>Error JSON shape:</p>
<pre>{{
  "success": false,
  "message": "Email already used",
  "data": null,
  "errors": {{}}
}}</pre>

<h2>8. Validation errors (422)</h2>
<p>Pair with the Validation engine:</p>
<pre>from tpy.validation import validate, ValidationException
from tpy.http import ApiResponse

try:
    data = validate(payload, {{
        "email": "required|email",
        "age": "required|integer|min:18",
    }})
except ValidationException as exc:
    return ApiResponse.validation_error(exc)

return ApiResponse.success(data)</pre>
<p><code>validation_error</code> reads <code>exc.first_messages()</code> when you pass the exception, and returns HTTP 422 with an <code>errors</code> object keyed by field.</p>

<h2>9. Method cheat sheet</h2>
<table class="doc-table">
  <thead><tr><th>Method</th><th>Status</th><th>When</th></tr></thead>
  <tbody>
    <tr><td><code>success</code></td><td>200</td><td>Normal read/update</td></tr>
    <tr><td><code>created</code></td><td>201</td><td>Resource created</td></tr>
    <tr><td><code>paginated</code></td><td>200</td><td>List with meta</td></tr>
    <tr><td><code>error</code></td><td>400+</td><td>Custom failure</td></tr>
    <tr><td><code>validation_error</code></td><td>422</td><td>Invalid input</td></tr>
    <tr><td><code>not_found</code></td><td>404</td><td>Missing resource</td></tr>
    <tr><td><code>unauthorized</code></td><td>401</td><td>Auth missing/bad</td></tr>
    <tr><td><code>forbidden</code></td><td>403</td><td>Authenticated but denied</td></tr>
    <tr><td><code>no_content</code></td><td>204</td><td>Delete with empty body</td></tr>
    <tr><td><code>payload</code> / <code>json</code></td><td>custom</td><td>Build envelope manually</td></tr>
  </tbody>
</table>

<h2>10. Common mistakes</h2>
<ul>
  <li>Returning a raw <code>dict</code> from some routes and <code>ApiResponse</code> from others — clients break.</li>
  <li>Putting error details only in <code>message</code> and leaving <code>errors</code> empty when you have field-level problems.</li>
  <li>Forgetting that <code>paginated()</code> needs a paginator/<code>data</code>+<code>meta</code> dict — not a bare list.</li>
</ul>
""",
    },
    {
        "file": "validation.html",
        "tag": "Platform 08 · Study guide",
        "title": "Validation engine",
        "lead": "Validate request payloads with pipe rules before they reach your services.",
        "prev": ("api-response.html", "ApiResponse helpers"),
        "next": ("kernel.html", "Application kernel"),
        "body": f"""
{goals(
    "How to call validate() with rule strings",
    "How ValidationException becomes an API error",
    "How to register a custom rule",
)}

<h2>1. Setup</h2>
<pre>from tpy.validation import validate, ValidationException, Validator
from tpy.http import ApiResponse</pre>
<p>No extra dependency. Use in controllers/services on incoming dict payloads.</p>

<h2>2. Basic usage</h2>
<pre>try:
    data = validate(
        payload,
        {{
            "email": "required|email",
            "age": "required|integer|min:18",
            "password": "required|confirmed",
            "role": "nullable|in:admin,user",
        }},
    )
except ValidationException as exc:
    return ApiResponse.validation_error(exc)

# data is the cleaned/accepted input
return ApiResponse.success(service.create(data))</pre>

<h2>3. How it works</h2>
<ol>
  <li>Rules are pipe-separated strings (<code>required|email|min:3</code>).</li>
  <li>The engine runs each rule in order for every field.</li>
  <li>On failure it raises <code>ValidationException</code> with per-field messages.</li>
  <li><code>ApiResponse.validation_error(exc)</code> turns that into HTTP 422 JSON.</li>
</ol>

<table class="doc-table">
  <thead><tr><th>Rule</th><th>Example</th><th>Meaning</th></tr></thead>
  <tbody>
    <tr><td><code>required</code></td><td><code>required</code></td><td>Must be present/non-empty</td></tr>
    <tr><td><code>nullable</code></td><td><code>nullable|email</code></td><td>Skip other rules when empty</td></tr>
    <tr><td><code>email</code> / <code>uuid</code> / <code>url</code></td><td><code>email</code></td><td>Format checks</td></tr>
    <tr><td><code>integer</code> / <code>numeric</code> / <code>boolean</code></td><td><code>integer</code></td><td>Type checks</td></tr>
    <tr><td><code>min</code> / <code>max</code> / <code>between</code></td><td><code>min:18</code></td><td>Bounds</td></tr>
    <tr><td><code>in</code> / <code>not_in</code></td><td><code>in:admin,user</code></td><td>Allow-list</td></tr>
    <tr><td><code>confirmed</code></td><td><code>confirmed</code></td><td>Needs <code>field_confirmation</code></td></tr>
    <tr><td><code>regex</code></td><td><code>regex:^[A-Z]+$</code></td><td>Pattern</td></tr>
  </tbody>
</table>

<h2>4. Custom rules</h2>
<pre>Validator.extend(
    "odd",
    lambda attr, value, data: int(value) % 2 == 1,
    "Value must be odd.",
)
Validator.make({{"n": 3}}, {{"n": "odd"}}).validate()</pre>
""",
    },
    {
        "file": "kernel.html",
        "tag": "Platform 09–10 · Study guide",
        "title": "Application kernel",
        "lead": "Boot services through Application, providers, and optional plugins — dual-mode with FastAPI.",
        "prev": ("validation.html", "Validation engine"),
        "next": ("middleware-health.html", "Middleware · Health · Lifecycle"),
        "body": f"""
{goals(
    "create() vs mount() modes",
    "How ServiceProviders register and boot",
    "How to resolve services from the container",
)}

<h2>1. Setup — recommended create()</h2>
<pre>from tpy.kernel import Application

def create_app():
    return (
        Application(base_path=".")
        .with_framework_providers()
        .register(AppServiceProvider)
        .create(title="My App")
    )</pre>
<p>Point uvicorn at this factory, or call it from <code>app/main.py</code>.</p>

<h2>2. Setup — mount onto existing FastAPI</h2>
<pre>from fastapi import FastAPI
from tpy.kernel import Application

api = FastAPI()
Application(".").with_framework_providers().mount(api)
# api.state.tpy is the Application</pre>

<h2>3. How providers work</h2>
<pre>from tpy.kernel import ServiceProvider, Application
from tpy.cache import Cache, MemoryStore

class CacheServiceProvider(ServiceProvider):
    def register(self, app: Application) -> None:
        app.singleton("cache", lambda c: Cache(MemoryStore()))

    def boot(self, app: Application) -> None:
        # all bindings exist; safe to resolve
        app.make("cache").put("booted", True, ttl=30)</pre>
<ol>
  <li>Every provider <code>register()</code> runs first (bindings only).</li>
  <li>Then every <code>boot()</code> runs (can resolve dependencies).</li>
  <li>Fetch services with <code>app.make("cache")</code>.</li>
</ol>

<div class="callout">Generated <code>app/main.py</code> still works without the kernel (soft-break). Adopt Application when you need shared services, plugins, lifecycle, and health wiring.</div>
""",
    },
    {
        "file": "middleware-health.html",
        "tag": "Platform 11–13 · Study guide",
        "title": "Middleware · Health · Lifecycle",
        "lead": "Group HTTP middleware, expose health probes, and hook boot/request/shutdown events.",
        "prev": ("kernel.html", "Application kernel"),
        "next": ("logging-config.html", "Logging & Config"),
        "body": f"""
{goals(
    "What middleware groups are for",
    "Difference between /health and /health/ready",
    "Which lifecycle hooks exist",
)}

<h2>1. Setup</h2>
<p>Use the Application kernel so middleware, health, and lifecycle register together:</p>
<pre>app = Application(".").with_framework_providers().create()</pre>

<h2>2. Middleware groups</h2>
<p><code>MiddlewareManager</code> lets you name stacks (for example <code>web</code>, <code>api</code>, <code>auth</code>) and attach them to routes. Keep cross-cutting concerns (logging, auth headers, CORS wrappers) out of every controller.</p>

<h2>3. Health checks</h2>
<table class="doc-table">
  <thead><tr><th>Endpoint</th><th>Meaning</th></tr></thead>
  <tbody>
    <tr><td><code>GET /health</code></td><td>Process alive</td></tr>
    <tr><td><code>GET /health/ready</code></td><td>Dependencies ready (when checks are registered)</td></tr>
  </tbody>
</table>

<h2>4. Lifecycle hooks</h2>
<ul>
  <li><code>boot</code> — app starting</li>
  <li><code>shutdown</code> — app stopping</li>
  <li><code>before</code> / <code>after</code> — around a request</li>
  <li><code>exception</code> — centralized error observation</li>
</ul>
<p>Use hooks for metrics, audit logs, or cleanup — not for primary business rules (those stay in services).</p>
""",
    },
    {
        "file": "logging-config.html",
        "tag": "Platform 14–15 · Study guide",
        "title": "Logging &amp; Config",
        "lead": "Configure nested settings and write structured logs — including production config caching.",
        "prev": ("middleware-health.html", "Middleware · Health · Lifecycle"),
        "next": ("storage-routes.html", "Storage & route cache"),
        "body": f"""
{goals(
    "How Config.load / load_auto work",
    "How to cache config for faster boots",
    "How to write to log channels",
)}

<h2>1. Configuration setup</h2>
<pre>from tpy.config import Config

# Always parse tpy.toml + env
cfg = Config.load(".")

# Prefer JSON cache when TPY_CONFIG_CACHE=1 and cache is fresh
cfg = Config.load_auto(".")

print(cfg.get("app.name"))
print(cfg.get("database.driver"))
print(cfg.get("server.port", 8000))
cfg.set("cache.driver", "redis")  # runtime only</pre>

<pre><span class="prompt">$</span> tpy config show
<span class="prompt">$</span> tpy config show app.name
<span class="prompt">$</span> tpy config cache
<span class="prompt">$</span> tpy config status
<span class="prompt">$</span> tpy config clear
<span class="prompt">$</span> set TPY_CONFIG_CACHE=1   <span style="color:var(--muted)"># Windows</span></pre>

<h2>2. How config caching works</h2>
<ol>
  <li><code>tpy config cache</code> writes <code>storage/framework/config.cache.json</code>.</li>
  <li>Cache is <strong style="color:var(--ink);">fresh</strong> only if newer than <code>tpy.toml</code> and <code>.env</code>.</li>
  <li>With <code>TPY_CONFIG_CACHE=1</code>, <code>load_auto()</code> reads the cache when fresh; otherwise it reloads live sources.</li>
</ol>

<h2>3. Logging setup</h2>
<pre>from tpy.logging import get_logger, LogManager

log = get_logger("app")
log.info("booted", version="0.1.9")

manager = LogManager()
manager.configure(level="INFO", log_dir="storage/logs", app_name="myapp")
manager.channel("stack").error("something failed")</pre>
""",
    },
    {
        "file": "storage-routes.html",
        "tag": "Platform 16–17 · Study guide",
        "title": "Storage &amp; route cache",
        "lead": "Store files on disk (S3-ready API) and cache the route table for ops tooling.",
        "prev": ("logging-config.html", "Logging & Config"),
        "next": ("cli-watch.html", "Optimize · CLI · Watch"),
        "body": f"""
{goals(
    "How to read/write files via Storage",
    "How to build and list a route cache",
    "How optimize ties config + routes together",
)}

<h2>1. File storage setup</h2>
<pre>from tpy.storage import Storage

disk = Storage.disk("local")
disk.put("reports/hello.txt", b"hello")
raw = disk.get("reports/hello.txt")
disk.delete("reports/hello.txt")</pre>
<p>Local files land under the project storage disk root. The API is intentionally driver-shaped so an S3 disk can plug in later without rewriting callers.</p>

<h2>2. Route cache setup</h2>
<pre><span class="prompt">$</span> tpy serve   <span style="color:var(--muted)"># app must import cleanly</span>
<span class="prompt">$</span> tpy route cache --app app.main:app
<span class="prompt">$</span> tpy route list --cached
<span class="prompt">$</span> tpy route clear</pre>
<p>Writes <code>storage/framework/routes.cache.json</code> by importing your FastAPI app and collecting routes.</p>

<h2>3. How route cache helps</h2>
<ul>
  <li>Inspect routes without booting heavy middleware every time.</li>
  <li>Ship a snapshot for ops/docs generation.</li>
  <li>Combine with <code>tpy optimize</code> for production warm caches.</li>
</ul>
""",
    },
    {
        "file": "cli-watch.html",
        "tag": "Platform 18–20 · Study guide",
        "title": "Optimize · CLI · Watch",
        "lead": "Ship faster boots, explore the CLI professionally, and rebuild when schema.tpy changes.",
        "prev": ("storage-routes.html", "Storage & route cache"),
        "next": None,
        "body": f"""
{goals(
    "How tpy optimize prepares production caches",
    "Which DX commands to use daily",
    "How watch mode rebuilds on schema edits",
)}

<h2>1. Optimize (config + routes)</h2>
<pre><span class="prompt">$</span> tpy optimize
<span class="prompt">$</span> tpy optimize --skip-routes
<span class="prompt">$</span> set TPY_CONFIG_CACHE=1</pre>
<ol>
  <li>Writes config cache JSON.</li>
  <li>Imports the app and writes route cache (unless <code>--skip-routes</code>).</li>
  <li>With <code>TPY_CONFIG_CACHE=1</code>, boots prefer the fresh config cache.</li>
</ol>

<h2>2. Better CLI (study these first)</h2>
<table class="doc-table">
  <thead><tr><th>Command</th><th>What it teaches you</th></tr></thead>
  <tbody>
    <tr><td><code>tpy -V</code> / <code>tpy version</code></td><td>Installed framework version</td></tr>
    <tr><td><code>tpy about</code></td><td>Env + project diagnostics</td></tr>
    <tr><td><code>tpy commands</code></td><td>Full command map</td></tr>
    <tr><td><code>tpy doctor</code></td><td>Scaffold health</td></tr>
  </tbody>
</table>

<h2>3. Watch mode setup</h2>
<pre><span class="prompt">#</span> terminal A — API
<span class="prompt">$</span> tpy serve --reload

<span class="prompt">#</span> terminal B — schema rebuilds
<span class="prompt">$</span> tpy watch
<span class="prompt">$</span> tpy watch --with-db
<span class="prompt">$</span> tpy watch --interval 0.5</pre>

<h2>4. How watch works</h2>
<ol>
  <li>Polls mtimes of <code>schema.tpy</code> and <code>tpy.toml</code> (stdlib only — no extra deps).</li>
  <li>On change, runs <code>tpy build --skip-db</code> (or full build with <code>--with-db</code>).</li>
  <li>You still run <code>tpy migrate</code> yourself when tables change.</li>
</ol>

<div class="callout">Watch rebuilds code. Migrate changes the database. Serve reloads Python. All three are separate on purpose.</div>
""",
    },
]
