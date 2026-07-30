async function request(path, options = {}) {
  const res = await fetch(`/api/studio${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    const detail = data?.detail || data?.error || text || res.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export const api = {
  health: () => request("/health"),
  getSchema: () => request("/schema"),
  previewSchema: (body) =>
    request("/schema/preview", { method: "POST", body: JSON.stringify(body) }),
  saveSchema: (body) =>
    request("/schema/save", { method: "POST", body: JSON.stringify(body) }),
  getDatabase: () => request("/database"),
  postDatabase: (body) =>
    request("/database", { method: "POST", body: JSON.stringify(body) }),
  getAuth: () => request("/auth"),
  postAuth: (body) =>
    request("/auth", { method: "POST", body: JSON.stringify(body) }),
  getRoutes: () => request("/routes"),
  getTemplates: () => request("/templates"),
  applyTemplate: (body) =>
    request("/templates/apply", { method: "POST", body: JSON.stringify(body) }),
};

export async function streamCommand(path, body, onEvent) {
  const res = await fetch(`/api/studio${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const line = chunk
        .split("\n")
        .find((l) => l.startsWith("data: "));
      if (!line) continue;
      try {
        onEvent(JSON.parse(line.slice(6)));
      } catch {
        /* ignore malformed */
      }
    }
  }
}
