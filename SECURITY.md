# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
| < 0.1   | No        |

## Reporting a vulnerability

Please **do not** open a public issue for security-sensitive reports.

Prefer:

1. GitHub Security Advisories for this repository, or
2. A private message to the maintainer via the contact on
   [the portfolio site](https://selvacv.lovable.app).

Include steps to reproduce, impact, and any suggested fix. We aim to
acknowledge reports within a reasonable time and coordinate disclosure.

## Auth / JWT hardening (generated apps)

When using `tpy auth`:

- **Never** ship with a missing or weak `JWT_SECRET`. The generated JWT helper
  fails closed if the secret is unset or known-weak.
- Bootstrap credentials are written to `storage/auth_bootstrap.txt` (keep
  `storage/` gitignored). Change the password after first login.
- Generated `/auth/login` includes a simple in-memory rate limit. For
  production, put Redis, Cloudflare, or API-gateway rate limits in front of
  auth endpoints.
- Do not log passwords or JWT secrets.

## Dependency extras

Install only the database drivers you need (`tamilPY[postgres]`, etc.) to
reduce supply-chain surface area.
