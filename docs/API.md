# API / DRF policy (M-010)

## Current product surface

Al-Madrasatul Rasulillah MIS is **Django SSR** (HTML templates). There is **no domain REST API** for wanafunzi, mahudhurio, malipo, n.k.

| Endpoint | Status |
|----------|--------|
| `/` | Health ping (`Muunganisho umefanikiwa!`) — always on |
| `/madrasa/…` | App (session auth) |
| `/admin/` | Django admin |
| `/api-token-auth/` | **Opt-in** DRF `obtain_auth_token` only |

## Token auth gate

- Setting: `ENABLE_TOKEN_AUTH` ← env `DJANGO_ENABLE_TOKEN_AUTH` (default **False**)
- When False: URL is **not registered** (404)
- When True: POST username/password → token (DRF Authtoken). Anon throttle `30/hour`.

```bash
# .env (lab only)
DJANGO_ENABLE_TOKEN_AUTH=True
```

**Production:** keep False unless you ship a real mobile/API product with HTTPS, scoped permissions, and rate limits reviewed.

## Future API

If a mobile app is needed later, add versioned endpoints under `/api/v1/` with explicit serializers/permissions — do not treat token-auth alone as an API.
