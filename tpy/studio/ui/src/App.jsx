import { useCallback, useEffect, useMemo, useState } from "react";
import { api, streamCommand } from "./api.js";

const FIELD_TYPES = ["int", "string", "float", "bool", "uuid", "datetime", "enum"];
const CONSTRAINTS = ["primary", "required", "unique", "nullable", "index"];
const TABS = [
  "Models",
  "Relations",
  "Database",
  "Auth",
  "Diff",
  "Build",
  "API",
  "Templates",
];

function emptyField() {
  return {
    name: "field",
    type: "string",
    constraints: [],
    default: null,
    has_default: false,
    enum_values: [],
    references: null,
  };
}

function emptyModel(name = "Model") {
  return {
    name,
    fields: [
      {
        name: "id",
        type: "uuid",
        constraints: ["primary"],
        default: null,
        has_default: false,
        enum_values: [],
        references: null,
      },
    ],
    unique_together: [],
    relations: [],
  };
}

function validateSchema(schema) {
  const errors = [];
  const names = new Map();
  (schema.models || []).forEach((model, mi) => {
    if (names.has(model.name)) {
      errors.push(`Duplicate model '${model.name}'`);
    }
    names.set(model.name, mi);
    const fields = new Set();
    (model.fields || []).forEach((field) => {
      if (fields.has(field.name)) {
        errors.push(`Duplicate field '${field.name}' in ${model.name}`);
      }
      fields.add(field.name);
      if (field.references?.model && !names.has(field.references.model) &&
          !(schema.models || []).some((m) => m.name === field.references.model)) {
        errors.push(
          `${model.name}.${field.name} references undefined '${field.references.model}'`
        );
      }
    });
  });
  return errors;
}

export default function App() {
  const [tab, setTab] = useState("Models");
  const [schema, setSchema] = useState(null);
  const [auth, setAuth] = useState(null);
  const [db, setDb] = useState(null);
  const [diff, setDiff] = useState("");
  const [diagnostics, setDiagnostics] = useState([]);
  const [log, setLog] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [openApi, setOpenApi] = useState(null);
  const [tryReq, setTryReq] = useState({ method: "GET", path: "/", body: "{}" });
  const [tryRes, setTryRes] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const [s, a, d, h, t] = await Promise.all([
        api.getSchema(),
        api.getAuth(),
        api.getDatabase(),
        api.health(),
        api.getTemplates(),
      ]);
      setSchema(s);
      setAuth(a);
      setDb(d);
      setHealth(h);
      setTemplates(t.templates || []);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const localErrors = useMemo(
    () => (schema ? validateSchema(schema) : []),
    [schema]
  );

  async function preview() {
    const result = await api.previewSchema(schema);
    setDiff(result.diff || "(no changes)");
    setDiagnostics(result.diagnostics || []);
    setTab("Diff");
  }

  async function save() {
    const saved = await api.saveSchema(schema);
    setSchema(saved);
    setDiff("");
    alert("schema.tpy saved");
  }

  async function runStream(path, body) {
    setBusy(true);
    setLog("");
    setTab("Build");
    try {
      await streamCommand(path, body, (evt) => {
        if (evt.type === "stdout" || evt.type === "stderr") {
          setLog((prev) => prev + (evt.text || ""));
        } else if (evt.type === "exit") {
          setLog((prev) => prev + `\n[exit ${evt.code}]\n`);
        }
      });
    } catch (err) {
      setLog((prev) => prev + `\nERROR: ${err.message}\n`);
    } finally {
      setBusy(false);
    }
  }

  if (!schema) {
    return (
      <div className="main">
        <p className="muted">Loading Studio…</p>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>tamilPY Studio</h1>
        <span className="muted">
          {health?.version} {health?.ui_built ? "" : "(UI src)"}
        </span>
        <nav className="tabs">
          {TABS.map((name) => (
            <button
              key={name}
              type="button"
              className={tab === name ? "active" : ""}
              onClick={() => setTab(name)}
            >
              {name}
            </button>
          ))}
        </nav>
        <div className="row" style={{ marginLeft: "auto" }}>
          <button type="button" className="secondary" onClick={load}>
            Reload
          </button>
          <button type="button" className="secondary" onClick={preview}>
            Preview diff
          </button>
          <button type="button" onClick={save} disabled={localErrors.length > 0}>
            Save
          </button>
        </div>
      </header>
      <main className="main">
        {error && <p className="error">{error}</p>}
        {localErrors.length > 0 && (
          <div className="panel" style={{ marginBottom: "1rem" }}>
            {localErrors.map((e) => (
              <div key={e} className="field-error">
                {e}
              </div>
            ))}
          </div>
        )}
        {tab === "Models" && (
          <ModelsPanel schema={schema} setSchema={setSchema} />
        )}
        {tab === "Relations" && (
          <RelationsPanel schema={schema} setSchema={setSchema} />
        )}
        {tab === "Database" && (
          <DatabasePanel db={db} setDb={setDb} onSaved={load} />
        )}
        {tab === "Auth" && (
          <AuthPanel auth={auth} setAuth={setAuth} />
        )}
        {tab === "Diff" && (
          <div className="panel grid">
            <div className="row">
              <button type="button" onClick={preview}>
                Refresh preview
              </button>
              <button type="button" onClick={save} disabled={localErrors.length > 0}>
                Apply save
              </button>
            </div>
            {diagnostics.map((d) => (
              <div key={d.formatted} className={d.severity === "error" ? "error" : "muted"}>
                {d.formatted}
              </div>
            ))}
            <pre className="diff">{diff || "Click Preview diff to compare."}</pre>
          </div>
        )}
        {tab === "Build" && (
          <div className="panel grid">
            <div className="row">
              <button type="button" disabled={busy} onClick={() => runStream("/build")}>
                Build
              </button>
              <button type="button" disabled={busy} onClick={() => runStream("/migrate")}>
                Migrate
              </button>
              <button
                type="button"
                className="danger"
                disabled={busy}
                onClick={() => {
                  if (confirm("Roll back last migration?")) {
                    runStream("/migrate/rollback", { confirm: true });
                  }
                }}
              >
                Rollback
              </button>
              <button type="button" disabled={busy} onClick={() => runStream("/seed", {})}>
                Seed
              </button>
              <button type="button" disabled={busy} onClick={() => runStream("/serve")}>
                Serve
              </button>
            </div>
            <pre className="log">{log || "Command output streams here."}</pre>
          </div>
        )}
        {tab === "API" && (
          <ApiExplorer
            routes={routes}
            setRoutes={setRoutes}
            openApi={openApi}
            setOpenApi={setOpenApi}
            tryReq={tryReq}
            setTryReq={setTryReq}
            tryRes={tryRes}
            setTryRes={setTryRes}
          />
        )}
        {tab === "Templates" && (
          <TemplatesPanel
            templates={templates}
            onApplied={async (schemaNext) => {
              setSchema(schemaNext);
              await load();
            }}
          />
        )}
      </main>
    </div>
  );
}

function ModelsPanel({ schema, setSchema }) {
  function updateModel(index, next) {
    const models = [...schema.models];
    models[index] = next;
    setSchema({ ...schema, models });
  }

  function moveField(mi, fi, dir) {
    const model = { ...schema.models[mi], fields: [...schema.models[mi].fields] };
    const swap = fi + dir;
    if (swap < 0 || swap >= model.fields.length) return;
    [model.fields[fi], model.fields[swap]] = [model.fields[swap], model.fields[fi]];
    updateModel(mi, model);
  }

  return (
    <div className="panel">
      <div className="row" style={{ marginBottom: "0.75rem" }}>
        <button
          type="button"
          onClick={() =>
            setSchema({
              ...schema,
              models: [...schema.models, emptyModel(`Model${schema.models.length + 1}`)],
            })
          }
        >
          Add model
        </button>
        <label className="muted">
          database{" "}
          <select
            value={schema.database || "sqlite"}
            onChange={(e) => setSchema({ ...schema, database: e.target.value })}
          >
            {["sqlite", "postgres", "mysql", "mongodb"].map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
      </div>
      {schema.models.map((model, mi) => (
        <div className="model-card" key={`${model.name}-${mi}`}>
          <div className="row">
            <input
              value={model.name}
              onChange={(e) => updateModel(mi, { ...model, name: e.target.value })}
            />
            <button
              type="button"
              className="danger secondary"
              onClick={() =>
                setSchema({
                  ...schema,
                  models: schema.models.filter((_, i) => i !== mi),
                })
              }
            >
              Remove
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() =>
                updateModel(mi, {
                  ...model,
                  fields: [...model.fields, emptyField()],
                })
              }
            >
              Add field
            </button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Constraints</th>
                <th>Default</th>
                <th>References</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {model.fields.map((field, fi) => (
                <tr key={`${field.name}-${fi}`}>
                  <td>
                    <input
                      value={field.name}
                      onChange={(e) => {
                        const fields = [...model.fields];
                        fields[fi] = { ...field, name: e.target.value };
                        updateModel(mi, { ...model, fields });
                      }}
                    />
                  </td>
                  <td>
                    <select
                      value={field.type?.startsWith("enum:") ? "enum" : field.type}
                      onChange={(e) => {
                        const fields = [...model.fields];
                        const type = e.target.value;
                        fields[fi] = {
                          ...field,
                          type: type === "enum" ? "enum" : type,
                          enum_values: type === "enum" ? field.enum_values || ["a", "b"] : [],
                        };
                        updateModel(mi, { ...model, fields });
                      }}
                    >
                      {FIELD_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                    {(field.type === "enum" || field.type?.startsWith("enum")) && (
                      <input
                        placeholder="a,b,c"
                        value={(field.enum_values || []).join(",")}
                        onChange={(e) => {
                          const fields = [...model.fields];
                          fields[fi] = {
                            ...field,
                            type: "enum",
                            enum_values: e.target.value
                              .split(",")
                              .map((s) => s.trim())
                              .filter(Boolean),
                          };
                          updateModel(mi, { ...model, fields });
                        }}
                      />
                    )}
                  </td>
                  <td>
                    <div className="chips">
                      {CONSTRAINTS.map((c) => (
                        <span
                          key={c}
                          className={`chip ${(field.constraints || []).includes(c) ? "on" : ""}`}
                          onClick={() => {
                            const set = new Set(field.constraints || []);
                            if (set.has(c)) set.delete(c);
                            else set.add(c);
                            const fields = [...model.fields];
                            fields[fi] = { ...field, constraints: [...set] };
                            updateModel(mi, { ...model, fields });
                          }}
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td>
                    <input
                      value={field.has_default ? String(field.default ?? "") : ""}
                      placeholder="—"
                      onChange={(e) => {
                        const fields = [...model.fields];
                        const raw = e.target.value;
                        fields[fi] = {
                          ...field,
                          has_default: raw !== "",
                          default: raw,
                        };
                        updateModel(mi, { ...model, fields });
                      }}
                    />
                  </td>
                  <td>
                    <select
                      value={field.references?.model || ""}
                      onChange={(e) => {
                        const fields = [...model.fields];
                        const modelName = e.target.value;
                        fields[fi] = {
                          ...field,
                          references: modelName
                            ? {
                                model: modelName,
                                table: modelName.toLowerCase(),
                                column: "id",
                                on_delete: null,
                                on_update: null,
                              }
                            : null,
                        };
                        updateModel(mi, { ...model, fields });
                      }}
                    >
                      <option value="">—</option>
                      {schema.models.map((m) => (
                        <option key={m.name} value={m.name}>
                          {m.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <button type="button" className="secondary" onClick={() => moveField(mi, fi, -1)}>
                      ↑
                    </button>
                    <button type="button" className="secondary" onClick={() => moveField(mi, fi, 1)}>
                      ↓
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() =>
                        updateModel(mi, {
                          ...model,
                          fields: model.fields.filter((_, i) => i !== fi),
                        })
                      }
                    >
                      ×
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

function RelationsPanel({ schema, setSchema }) {
  const [positions, setPositions] = useState(() => {
    const pos = {};
    schema.models.forEach((m, i) => {
      pos[m.name] = { x: 40 + (i % 4) * 160, y: 40 + Math.floor(i / 4) * 100 };
    });
    return pos;
  });
  const [draft, setDraft] = useState(null);
  const [drag, setDrag] = useState(null);

  function onMouseMove(e) {
    if (!drag) return;
    const rect = e.currentTarget.getBoundingClientRect();
    setPositions((prev) => ({
      ...prev,
      [drag]: {
        x: e.clientX - rect.left - 40,
        y: e.clientY - rect.top - 16,
      },
    }));
  }

  function addRelation() {
    if (!draft?.from || !draft?.to || !draft?.kind) return;
    const models = schema.models.map((m) => {
      if (m.name !== draft.from) return m;
      return {
        ...m,
        relations: [
          ...(m.relations || []),
          {
            kind: draft.kind,
            model: draft.to,
            name: draft.alias || draft.to.toLowerCase(),
            foreign_key: draft.via || null,
            local_key: null,
            through: draft.through || null,
            pivot_foreign_key: null,
            pivot_related_key: null,
          },
        ],
      };
    });
    setSchema({ ...schema, models });
    setDraft(null);
  }

  const edges = [];
  schema.models.forEach((m) => {
    (m.relations || []).forEach((r, idx) => {
      edges.push({ from: m.name, to: r.model, kind: r.kind, idx, name: r.name });
    });
  });

  return (
    <div className="panel grid">
      <p className="muted">Drag nodes. Click two models then set relation type.</p>
      <div className="row">
        <select
          value={draft?.from || ""}
          onChange={(e) => setDraft({ ...(draft || {}), from: e.target.value })}
        >
          <option value="">From</option>
          {schema.models.map((m) => (
            <option key={m.name} value={m.name}>
              {m.name}
            </option>
          ))}
        </select>
        <select
          value={draft?.to || ""}
          onChange={(e) => setDraft({ ...(draft || {}), to: e.target.value })}
        >
          <option value="">To</option>
          {schema.models.map((m) => (
            <option key={m.name} value={m.name}>
              {m.name}
            </option>
          ))}
        </select>
        <select
          value={draft?.kind || ""}
          onChange={(e) => setDraft({ ...(draft || {}), kind: e.target.value })}
        >
          <option value="">Type</option>
          <option value="belongs_to">belongs_to</option>
          <option value="has_many">has_many</option>
          <option value="has_one">has_one</option>
          <option value="belongs_to_many">belongs_to_many</option>
        </select>
        <input
          placeholder="alias"
          value={draft?.alias || ""}
          onChange={(e) => setDraft({ ...(draft || {}), alias: e.target.value })}
        />
        <input
          placeholder="via / through"
          value={draft?.via || draft?.through || ""}
          onChange={(e) => {
            const v = e.target.value;
            setDraft({
              ...(draft || {}),
              via: draft?.kind === "belongs_to_many" ? null : v,
              through: draft?.kind === "belongs_to_many" ? v : null,
            });
          }}
        />
        <button type="button" onClick={addRelation}>
          Add edge
        </button>
      </div>
      <div className="canvas" onMouseMove={onMouseMove} onMouseUp={() => setDrag(null)}>
        <svg width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
          {edges.map((e) => {
            const a = positions[e.from] || { x: 0, y: 0 };
            const b = positions[e.to] || { x: 100, y: 100 };
            return (
              <g key={`${e.from}-${e.to}-${e.idx}`}>
                <line
                  x1={a.x + 60}
                  y1={a.y + 16}
                  x2={b.x + 60}
                  y2={b.y + 16}
                  stroke="#3d8bfd"
                  strokeWidth="2"
                />
                <text x={(a.x + b.x) / 2 + 60} y={(a.y + b.y) / 2} fill="#8b9bb4" fontSize="11">
                  {e.kind}
                </text>
              </g>
            );
          })}
        </svg>
        {schema.models.map((m) => (
          <div
            key={m.name}
            className="node"
            style={{ left: positions[m.name]?.x || 0, top: positions[m.name]?.y || 0 }}
            onMouseDown={() => setDrag(m.name)}
          >
            <strong>{m.name}</strong>
            <div className="muted">{(m.relations || []).length} rel</div>
          </div>
        ))}
      </div>
      <ul>
        {edges.map((e) => (
          <li key={`${e.from}-${e.idx}`}>
            {e.from} —{e.kind}→ {e.to} ({e.name}){" "}
            <button
              type="button"
              className="secondary"
              onClick={() => {
                const models = schema.models.map((m) => {
                  if (m.name !== e.from) return m;
                  return {
                    ...m,
                    relations: (m.relations || []).filter((_, i) => i !== e.idx),
                  };
                });
                setSchema({ ...schema, models });
              }}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function DatabasePanel({ db, setDb, onSaved }) {
  const [form, setForm] = useState({
    provider: db?.provider || "sqlite",
    path: "database/database.sqlite3",
    host: "127.0.0.1",
    port: "",
    database_name: "tpy",
    username: "",
    password: "",
  });
  const [msg, setMsg] = useState("");

  async function submit(dryRun) {
    setMsg("");
    try {
      const payload = { ...form, dry_run: dryRun };
      if (form.provider === "sqlite") payload.database_url = form.path;
      const result = await api.postDatabase(payload);
      setMsg(result.ok ? (dryRun ? "Connection OK" : "Saved") : `Failed: ${result.error}`);
      if (!dryRun) {
        setDb(result.config);
        onSaved?.();
      }
    } catch (err) {
      setMsg(err.message);
    }
  }

  return (
    <div className="panel grid">
      <div className="row">
        {["sqlite", "postgres", "mysql", "mongodb"].map((p) => (
          <label key={p}>
            <input
              type="radio"
              checked={form.provider === p}
              onChange={() => setForm({ ...form, provider: p })}
            />{" "}
            {p}
          </label>
        ))}
      </div>
      {form.provider === "sqlite" ? (
        <label>
          Path{" "}
          <input
            value={form.path}
            onChange={(e) => setForm({ ...form, path: e.target.value })}
          />
        </label>
      ) : (
        <div className="grid">
          <input placeholder="host" value={form.host} onChange={(e) => setForm({ ...form, host: e.target.value })} />
          <input placeholder="port" value={form.port} onChange={(e) => setForm({ ...form, port: e.target.value })} />
          <input placeholder="database" value={form.database_name} onChange={(e) => setForm({ ...form, database_name: e.target.value })} />
          <input placeholder="username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
          <input type="password" placeholder="password (write-only)" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </div>
      )}
      <div className="row">
        <button type="button" className="secondary" onClick={() => submit(true)}>
          Test connection
        </button>
        <button type="button" onClick={() => submit(false)}>
          Save
        </button>
      </div>
      {msg && <p className={msg.includes("Fail") ? "error" : "ok"}>{msg}</p>}
      <pre className="mono">{JSON.stringify(db?.env || db, null, 2)}</pre>
    </div>
  );
}

function AuthPanel({ auth, setAuth }) {
  const [roles, setRoles] = useState((auth?.roles || []).join(", "));
  const [email, setEmail] = useState(auth?.bootstrap_email || "");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");

  async function save(enabled) {
    try {
      const next = await api.postAuth({
        enabled,
        roles: roles.split(",").map((s) => s.trim()).filter(Boolean),
        bootstrap_email: email,
        bootstrap_password: password || null,
      });
      setAuth(next);
      setPassword("");
      setMsg("Auth settings saved");
    } catch (err) {
      setMsg(err.message);
    }
  }

  return (
    <div className="panel grid">
      <label>
        <input
          type="checkbox"
          checked={!!auth?.enabled}
          onChange={(e) => save(e.target.checked)}
        />{" "}
        Enable JWT auth (runs tpy auth when turned on)
      </label>
      <label>
        Roles{" "}
        <input value={roles} onChange={(e) => setRoles(e.target.value)} style={{ width: "100%" }} />
      </label>
      <label>
        Bootstrap email{" "}
        <input value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      <label>
        Bootstrap password {auth?.bootstrap_password_set ? "(set)" : ""}{" "}
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      </label>
      <button type="button" onClick={() => save(auth?.enabled)}>
        Save roles / bootstrap
      </button>
      {msg && <p className="muted">{msg}</p>}
    </div>
  );
}

function ApiExplorer({ routes, setRoutes, openApi, setOpenApi, tryReq, setTryReq, tryRes, setTryRes }) {
  useEffect(() => {
    api.getRoutes().then((r) => setRoutes(r.routes || [])).catch(() => {});
    fetch("http://127.0.0.1:8000/openapi.json")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setOpenApi(data))
      .catch(() => setOpenApi(null));
  }, [setRoutes, setOpenApi]);

  async function send() {
    try {
      const res = await fetch(`http://127.0.0.1:8000${tryReq.path}`, {
        method: tryReq.method,
        headers: { "Content-Type": "application/json" },
        body: ["POST", "PUT", "PATCH"].includes(tryReq.method) ? tryReq.body : undefined,
      });
      const text = await res.text();
      setTryRes(`${res.status}\n${text}`);
    } catch (err) {
      setTryRes(err.message);
    }
  }

  const paths = openApi?.paths ? Object.keys(openApi.paths) : [];

  return (
    <div className="panel grid">
      <p className="muted">
        {openApi ? "OpenAPI loaded from :8000" : "Dev server OpenAPI not reachable — showing cached/generated routes."}
      </p>
      <ul>
        {(routes || []).slice(0, 40).map((r, i) => (
          <li key={i}>
            <button
              type="button"
              className="secondary"
              onClick={() =>
                setTryReq({
                  ...tryReq,
                  method: (r.methods && r.methods[0]) || "GET",
                  path: r.path,
                })
              }
            >
              {(r.methods || []).join(",")} {r.path}
            </button>
          </li>
        ))}
        {paths.map((p) => (
          <li key={p} className="muted">
            {p}
          </li>
        ))}
      </ul>
      <div className="row">
        <select
          value={tryReq.method}
          onChange={(e) => setTryReq({ ...tryReq, method: e.target.value })}
        >
          {["GET", "POST", "PUT", "PATCH", "DELETE"].map((m) => (
            <option key={m}>{m}</option>
          ))}
        </select>
        <input
          style={{ flex: 1 }}
          value={tryReq.path}
          onChange={(e) => setTryReq({ ...tryReq, path: e.target.value })}
        />
        <button type="button" onClick={send}>
          Try it
        </button>
      </div>
      <textarea
        rows={5}
        value={tryReq.body}
        onChange={(e) => setTryReq({ ...tryReq, body: e.target.value })}
      />
      <pre className="log">{tryRes}</pre>
    </div>
  );
}

function TemplatesPanel({ templates, onApplied }) {
  const [diff, setDiff] = useState("");
  const [pending, setPending] = useState(null);

  async function preview(name) {
    const result = await api.applyTemplate({ name, confirm: false });
    setPending(name);
    setDiff(result.diff || "");
  }

  async function apply() {
    if (!pending) return;
    const result = await api.applyTemplate({ name: pending, confirm: true });
    setDiff(result.diff || "");
    if (result.schema) onApplied?.(result.schema);
    setPending(null);
  }

  return (
    <div className="panel grid">
      <ul>
        {templates.map((t) => (
          <li key={t.name} className="row">
            <strong>{t.name}</strong>
            <span className="muted">{t.description}</span>
            <button type="button" className="secondary" onClick={() => preview(t.name)}>
              Preview
            </button>
          </li>
        ))}
      </ul>
      {pending && (
        <div className="row">
          <button type="button" onClick={apply}>
            Apply {pending}
          </button>
          <button type="button" className="secondary" onClick={() => setPending(null)}>
            Cancel
          </button>
        </div>
      )}
      <pre className="diff">{diff}</pre>
    </div>
  );
}
