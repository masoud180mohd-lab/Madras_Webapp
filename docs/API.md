# API / DRF policy

## Surfaces

| Endpoint | Status |
|----------|--------|
| `/` | Health ping (`Muunganisho umefanikiwa!`) |
| `/madrasa/…` | SSR app (session + CSRF) |
| `/admin/` | Django admin |
| `/api/v1/` | **Staff mobile API** (JWT) |
| `/api-token-auth/` | **Opt-in** legacy DRF Authtoken — not a domain API |

## `/api/v1/` (P0)

Auth: `Authorization: Bearer <access>`. Access ~15 min, refresh ~7 days (rotated + blacklisted).

| Method | Path | CAP |
|--------|------|-----|
| `POST` | `/api/v1/auth/token/` | public (username + password) |
| `POST` | `/api/v1/auth/refresh/` | refresh token |
| `GET` | `/api/v1/me/` | authenticated — `cheo` + `capabilities` |
| `GET` | `/api/v1/madarasa/` | `view_directory` |
| `GET` | `/api/v1/madarasa/<id>/wanafunzi/` | `view_students` — hai tu; no parent phones |
| `GET` | `/api/v1/mahudhurio/?darasa=&tarehe=&aina_ya_rekodi=` | `attendance` |
| `POST` | `/api/v1/mahudhurio/` | `attendance` — batch, full active roster |

`POST` mahudhurio must include **every** active student in the class. Duplicate roll for the same `(darasa, tarehe, aina)` → **409** (`already_recorded`). Clients should treat 409 as successful sync, not a retry-with-new-rows error.

Permissions reuse `user_has_capability` / `CAP_*` — same matrix as the web app.

Throttle (production): anon `30/hour`, authenticated `300/hour`.

## Legacy token gate

- Setting: `ENABLE_TOKEN_AUTH` ← `DJANGO_ENABLE_TOKEN_AUTH` (default **False**)
- When False: `/api-token-auth/` is **not registered** (404)
- Do not use Authtoken as the mobile API. Use `/api/v1/auth/token/`.
