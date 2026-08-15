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
| `GET` | `/api/v1/mwanzo/` | authenticated — dashboard metrics |
| `GET` | `/api/v1/walimu/` | `view_directory` |
| `GET` | `/api/v1/wanafunzi/?q=&darasa=` | `view_students` — hai tu; no parent phones |
| `GET` | `/api/v1/wanafunzi/<id>/` | `view_students` — profile; parent phones only with `parent_contact` |
| `GET` | `/api/v1/watoro/` | `attendance` or `view_students` |
| `GET` | `/api/v1/malipo/` | `fees` |
| `GET` | `/api/v1/aina-malipo/` | `manage_students` |
| `GET` | `/api/v1/mwaka/` | `mseto` |
| `GET` | `/api/v1/hamisha/` | `promote_class` — class counts |
| `GET` | `/api/v1/mawasiliano/` | `parent_contact` — parent phones |
| `GET` | `/api/v1/ukaguzi/` | `manage_students` or `fees` |
| `GET` | `/api/v1/madarasa/` | `view_directory` |
| `GET` | `/api/v1/madarasa/<id>/wanafunzi/` | `view_students` — hai tu; no parent phones |
| `GET` | `/api/v1/mahudhurio/?darasa=&tarehe=&aina_ya_rekodi=` | `attendance` |
| `POST` | `/api/v1/mahudhurio/` | `attendance` — batch, full active roster |
| `GET` | `/api/v1/masomo/?darasa=` | `view_directory` |
| `POST` | `/api/v1/sabaq/` | `sabaq` — requires linked Mwalimu |
| `POST` | `/api/v1/maendeleo/` | `sabaq` — maendeleo ya mchana (not hifdhu) |
| `GET` | `/api/v1/mitihani/?somo=` | `exams` |
| `GET`/`PUT` | `/api/v1/mitihani/<id>/matokeo/` | `exams` — upsert maksi 0–100 |

`POST` mahudhurio must include **every** active student in the class. Duplicate roll for the same `(darasa, tarehe, aina)` → **409** (`already_recorded`). Clients should treat 409 as successful sync, not a retry-with-new-rows error.

Permissions reuse `user_has_capability` / `CAP_*` — same matrix as the web app.

`GET /media/...` accepts session **or** `Authorization: Bearer` (picha za wanafunzi kwenye app). Invalid Bearer → 401 JSON.

Throttle (production): anon `30/hour`, authenticated `300/hour`.

## Legacy token gate

- Setting: `ENABLE_TOKEN_AUTH` ← `DJANGO_ENABLE_TOKEN_AUTH` (default **False**)
- When False: `/api-token-auth/` is **not registered** (404)
- Do not use Authtoken as the mobile API. Use `/api/v1/auth/token/`.
