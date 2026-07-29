"""
Regenerate tamilPY GitHub Pages detail guides (study material).

Usage:
  py -3.12 scripts/build_docs_pages.py
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from docs_page_content import PAGES

DOCS = Path(__file__).resolve().parents[1] / "docs"
CSS_PATH = DOCS / "docs.css"

STUDY_CSS = dedent(
    """
    /* Clickable cards */
    a.tile{ text-decoration:none; color:inherit; display:block; cursor:pointer; }
    a.tile .more{
      display:inline-block; margin-top:0.85rem;
      font-family:"IBM Plex Mono", monospace; font-size:0.78rem;
      letter-spacing:0.04em; color:var(--amber);
    }
    a.tile:hover .more{ text-decoration:underline; }

    /* Detail / study pages */
    .page-hero{ padding:3.2rem 0 2.4rem; border-bottom:1px solid var(--line); }
    .page-hero h1{
      font-family:"Space Grotesk", sans-serif; font-weight:700;
      font-size:clamp(1.9rem, 3.6vw, 2.7rem); letter-spacing:-0.02em;
      line-height:1.08; margin:0 0 0.85rem;
    }
    .page-hero .lead{ max-width:44rem; }
    .crumb{
      display:flex; flex-wrap:wrap; gap:0.45rem; align-items:center;
      font-family:"IBM Plex Mono", monospace; font-size:0.78rem;
      color:var(--muted); margin-bottom:1.1rem;
    }
    .crumb a{ color:var(--muted); text-decoration:none; }
    .crumb a:hover{ color:var(--amber); }
    .crumb .sep{ opacity:0.5; }

    .doc-body{ padding:3rem 0 4.5rem; }
    .doc-body .prose{ max-width:820px; }
    .doc-body h2{
      margin:2.6rem 0 0.75rem;
      font-size:clamp(1.25rem, 2.4vw, 1.55rem);
    }
    .doc-body h2:first-child{ margin-top:0; }
    .doc-body h3{
      margin:1.4rem 0 0.5rem; font-size:1.05rem;
      font-family:"Space Grotesk", sans-serif;
    }
    .doc-body p{ color:var(--muted); margin:0 0 1rem; }
    .doc-body ul, .doc-body ol{
      margin:0 0 1.2rem; padding-left:1.15rem; color:var(--muted);
      display:grid; gap:0.45rem;
    }
    .doc-body li code, .doc-body p code, .doc-body .callout code{
      color:var(--amber); font-family:"IBM Plex Mono", monospace; font-size:0.9em;
    }
    .doc-body strong{ color:var(--ink); }
    .doc-body .callout{
      border:1px solid var(--line); border-left:2px solid var(--amber);
      background:rgba(9,28,50,0.55); padding:1rem 1.15rem;
      margin:1.2rem 0 1.5rem; color:var(--muted);
    }
    .doc-body .callout ul{ margin:0.55rem 0 0; }
    .doc-table{
      width:100%; border-collapse:collapse; margin:0 0 1.4rem; font-size:0.92rem;
    }
    .doc-table th, .doc-table td{
      border:1px solid var(--line); padding:0.65rem 0.8rem;
      text-align:left; vertical-align:top;
    }
    .doc-table th{
      font-family:"IBM Plex Mono", monospace; font-size:0.75rem;
      letter-spacing:0.06em; text-transform:uppercase; color:var(--amber);
      background:rgba(9,28,50,0.55);
    }
    .doc-table td{ color:var(--muted); }
    .doc-table code{
      color:var(--amber); font-family:"IBM Plex Mono", monospace; font-size:0.88em;
    }

    .pager{
      display:flex; flex-wrap:wrap; justify-content:space-between; gap:1rem;
      margin-top:2.8rem; padding-top:1.4rem; border-top:1px solid var(--line);
    }
    .pager a{
      text-decoration:none; font-family:"IBM Plex Mono", monospace; font-size:0.84rem;
      color:var(--ink); border:1px solid var(--line); padding:0.7rem 1rem;
      transition:border-color .18s ease, transform .18s ease;
    }
    .pager a:hover{ border-color:var(--amber); transform:translateY(-2px); }
    .pager .label{
      display:block; color:var(--muted); font-size:0.72rem;
      margin-bottom:0.25rem; letter-spacing:0.06em; text-transform:uppercase;
    }

    footer.site-footer{
      padding:2.2rem 0 2.8rem; border-top:1px solid var(--line);
      color:var(--muted); font-family:"IBM Plex Mono", monospace; font-size:0.84rem;
    }
    footer.site-footer .wrap{
      display:grid; gap:1.4rem;
      grid-template-columns: 1.3fr 1fr auto;
      align-items:start;
    }
    footer.site-footer .brand{
      color:var(--ink); margin:0 0 0.4rem;
      font-family:"Space Grotesk", sans-serif; font-weight:700; font-size:1rem;
    }
    footer.site-footer .blurb{ margin:0; max-width:28rem; line-height:1.55; }
    footer.site-footer .links{
      display:grid;
      grid-template-columns:repeat(2, minmax(0, 1fr));
      gap:0.55rem;
    }
    footer.site-footer .links a{
      color:var(--ink);
      text-decoration:none;
      border:1px solid var(--line);
      background:rgba(9,28,50,0.45);
      padding:0.75rem 0.85rem;
      min-height:2.75rem;
      display:flex;
      align-items:center;
    }
    footer.site-footer .links a:hover{
      color:var(--amber);
      border-color:var(--amber);
    }
    footer.site-footer .copy{ text-align:right; margin:0; }
    footer.site-footer .copy p{ margin:0; }
    @media (max-width: 860px){
      footer.site-footer{ padding:1.8rem 0 2.4rem; font-size:0.9rem; }
      footer.site-footer .wrap{ grid-template-columns:1fr; gap:1.2rem; }
      footer.site-footer .links{ grid-template-columns:1fr 1fr; gap:0.65rem; }
      footer.site-footer .links a{
        justify-content:center;
        text-align:center;
        padding:0.95rem 0.7rem;
        min-height:3rem;
      }
      footer.site-footer .copy{ text-align:left; padding-top:0.2rem; }
      .page-hero{ padding:2.4rem 0 1.8rem; }
      .doc-body{ padding:2.2rem 0 3.2rem; }
      .pager{ flex-direction:column; }
      .pager a{ width:100%; }
      .doc-table{ display:block; overflow-x:auto; -webkit-overflow-scrolling:touch; }
      .cta-row .btn{ width:100%; justify-content:center; }
    }
    @media (max-width: 420px){
      footer.site-footer .links{ grid-template-columns:1fr; }
    }
    """
).strip()


def ensure_css() -> None:
    raw = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else ""
    # Keep base theme (everything before clickable-card marker if present)
    marker = "/* Clickable cards */"
    base = raw.split(marker)[0].rstrip() if marker in raw else raw.rstrip()
    if not base:
        raise SystemExit("docs/docs.css missing base theme — restore from index styles")
    CSS_PATH.write_text(base + "\n\n" + STUDY_CSS + "\n", encoding="utf-8")


NAV_SCRIPT = """
<script>
(() => {
  const btn = document.querySelector(".nav-toggle");
  const menu = document.getElementById("site-menu");
  if (!btn || !menu) return;
  const setOpen = (open) => {
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.classList.toggle("nav-open", open);
    btn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  };
  btn.addEventListener("click", () => {
    setOpen(btn.getAttribute("aria-expanded") !== "true");
  });
  menu.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setOpen(false));
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });
})();
</script>
""".strip()


def render_page(page: dict) -> str:
    prev = page["prev"]
    nxt = page["next"]
    pager_left = (
        f'<a href="{prev[0]}"><span class="label">Previous</span>{prev[1]}</a>'
        if prev
        else "<span></span>"
    )
    pager_right = (
        f'<a href="{nxt[0]}"><span class="label">Next</span>{nxt[1]}</a>'
        if nxt
        else "<span></span>"
    )
    body = dedent(page["body"]).strip()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{page["title"]} — tamilPY Docs</title>
<meta name="description" content="{page["lead"]}" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="docs.css" />
</head>
<body>
<div class="crop tl"></div><div class="crop tr"></div><div class="crop bl"></div><div class="crop br"></div>

<nav class="nav">
  <div class="wrap nav-bar">
    <a class="logo" href="index.html"><span class="glyph">தமிழ்</span>PY</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-menu" aria-label="Open menu">
      <span></span><span></span><span></span>
    </button>
    <div class="navlinks" id="site-menu">
      <a href="index.html">Home</a>
      <a href="index.html#features">Features</a>
      <a href="index.html#platform">Platform</a>
      <a href="index.html#commands">CLI</a>
      <a href="schema.html">Schema</a>
      <a href="index.html#author">Author</a>
    </div>
  </div>
</nav>

<header class="page-hero">
  <div class="wrap">
    <div class="crumb">
      <a href="index.html">Docs</a>
      <span class="sep">/</span>
      <a href="index.html#features">Guides</a>
      <span class="sep">/</span>
      <span>{page["title"]}</span>
    </div>
    <p class="eyebrow">{page["tag"]}</p>
    <h1>{page["title"]}</h1>
    <p class="lead">{page["lead"]}</p>
    <div class="cta-row">
      <a class="btn btn-ghost" href="index.html#features">← All guides</a>
      <a class="btn btn-primary" href="index.html#install">Install tamilPY</a>
    </div>
  </div>
</header>

<section class="doc-body">
  <div class="wrap">
    <div class="prose">
{body}
      <div class="pager">
        {pager_left}
        {pager_right}
      </div>
    </div>
  </div>
</section>

<footer class="site-footer">
  <div class="wrap">
    <div>
      <p class="brand">tamilPY documentation</p>
      <p class="blurb">Client study guides for the schema-driven Python framework.</p>
    </div>
    <div class="links">
      <a href="index.html">Home</a>
      <a href="schema.html">Schema</a>
      <a href="api-response.html">ApiResponse</a>
      <a href="https://pypi.org/project/tamilPY/" target="_blank" rel="noopener noreferrer">PyPI</a>
      <a href="https://github.com/Selvaganapathiarumugam/tamilPY" target="_blank" rel="noopener noreferrer">GitHub</a>
    </div>
    <div class="copy">
      <p>© <a href="https://selvacv.lovable.app" target="_blank" rel="noopener noreferrer">Selvaganapathi Arumugam</a></p>
    </div>
  </div>
</footer>
{NAV_SCRIPT}
</body>
</html>
"""


def patch_index() -> None:
    index = DOCS / "index.html"
    html = index.read_text(encoding="utf-8")

    old_nav = """<nav class="nav">
  <div class="wrap">
    <a class="logo" href="#top"><span class="glyph">தமிழ்</span>PY</a>
    <div class="navlinks">
      <a href="#install">Install</a>
      <a href="#features">Features</a>
      <a href="#platform">Platform</a>
      <a href="#admin">Admin</a>
      <a href="#auth">Auth</a>
      <a href="schema.html">Schema</a>
      <a href="#commands">CLI</a>
      <a href="#guide">Guide</a>
      <a href="#author">Author</a>
    </div>
  </div>
</nav>"""

    new_nav = """<nav class="nav">
  <div class="wrap nav-bar">
    <a class="logo" href="#top"><span class="glyph">தமிழ்</span>PY</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-menu" aria-label="Open menu">
      <span></span><span></span><span></span>
    </button>
    <div class="navlinks" id="site-menu">
      <a href="#install">Install</a>
      <a href="#features">Features</a>
      <a href="#platform">Platform</a>
      <a href="#admin">Admin</a>
      <a href="#auth">Auth</a>
      <a href="schema.html">Schema</a>
      <a href="#commands">CLI</a>
      <a href="#guide">Guide</a>
      <a href="#author">Author</a>
    </div>
  </div>
</nav>"""

    if old_nav in html:
        html = html.replace(old_nav, new_nav)
    elif 'class="nav-toggle"' not in html:
        raise SystemExit("index nav pattern not found")

    old_footer = """<footer class="site-footer">
  <div class="wrap">
    <div>
      <p class="brand">tamilPY documentation</p>
      <p>Schema-driven FastAPI framework — client study guides.</p>
    </div>
    <div class="links">
      <a href="#features">Features</a>
      <a href="schema.html">Schema guide</a>
      <a href="api-response.html">ApiResponse</a>
      <a href="https://pypi.org/project/tamilPY/" target="_blank" rel="noopener noreferrer">PyPI</a>
      <a href="https://github.com/Selvaganapathiarumugam/tamilPY" target="_blank" rel="noopener noreferrer">GitHub</a>
    </div>
    <div class="copy">
      <p>© <a href="https://selvacv.lovable.app" target="_blank" rel="noopener noreferrer">Selvaganapathi Arumugam</a></p>
    </div>
  </div>
</footer>"""

    new_footer = """<footer class="site-footer">
  <div class="wrap">
    <div>
      <p class="brand">tamilPY documentation</p>
      <p class="blurb">Schema-driven FastAPI framework — client study guides.</p>
    </div>
    <div class="links">
      <a href="#features">Features</a>
      <a href="schema.html">Schema</a>
      <a href="api-response.html">ApiResponse</a>
      <a href="https://pypi.org/project/tamilPY/" target="_blank" rel="noopener noreferrer">PyPI</a>
      <a href="https://github.com/Selvaganapathiarumugam/tamilPY" target="_blank" rel="noopener noreferrer">GitHub</a>
    </div>
    <div class="copy">
      <p>© <a href="https://selvacv.lovable.app" target="_blank" rel="noopener noreferrer">Selvaganapathi Arumugam</a></p>
    </div>
  </div>
</footer>"""

    if old_footer in html:
        html = html.replace(old_footer, new_footer)

    if NAV_SCRIPT not in html:
        html = html.replace("</body>", f"{NAV_SCRIPT}\n</body>")

    index.write_text(html, encoding="utf-8")
    print("patched index.html nav/footer")


def main() -> None:
    ensure_css()
    for page in PAGES:
        path = DOCS / page["file"]
        path.write_text(render_page(page), encoding="utf-8")
        print("wrote", path.name)
    patch_index()
    print(f"done — {len(PAGES)} study guides")


if __name__ == "__main__":
    main()
