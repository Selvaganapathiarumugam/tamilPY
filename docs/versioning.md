# Versioning and deprecation (pre-1.0)

tamilPY follows **Semantic Versioning** once 1.0.0 ships. Until then:

## 0.x policy

- **Patch** (`0.1.x` → `0.1.y`): bug fixes, security hardening, docs, non-breaking generator improvements.
- **Minor** (`0.1` → `0.2`): new features; may include small breaking changes to generated code or DSL with a migration note in CHANGELOG.
- **Major** (`1.0.0`): stable public CLI, schema grammar, and extension points.

## Deprecation window

Before removing or renaming a public CLI flag, schema keyword, or documented
generator output contract:

1. Document the deprecation in CHANGELOG and docs.
2. Keep the old path working for **at least one minor** (or two patches on 0.x
   when feasible) with a warning when practical.
3. Remove in a subsequent release called out as breaking.

## Schema grammar

The grammar document is versioned as **v0.1** in
[schema-grammar.md](schema-grammar.md). Grammar bumps that break existing
`.tpy` files require a CHANGELOG entry and README callout.

## Support

Security-supported versions are listed in [SECURITY.md](../SECURITY.md).
