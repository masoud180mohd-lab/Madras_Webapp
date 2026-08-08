# Madras_Webapp

Mfumo wa usimamizi wa **Al-Madrasatul Rasulillah** (Mwera, Zanzibar).
Django server-rendered templates (HTML + CSS + vanilla JS), UI kwa Kiswahili.

## Mahitaji

- Python 3.9+ (Windows: tumia `py`, si `python` ikiwa PATH haiko)
- Pip packages kutoka `requirements.txt`

## Usanidi wa haraka (lab)

```bash
cd Madras_Webapp
py -m pip install -r requirements.txt
copy .env.example .env
py manage.py migrate
py manage.py runserver
```

Fungua: [http://127.0.0.1:8000/madrasa/ingia/](http://127.0.0.1:8000/madrasa/ingia/)

| Anwani | Maana |
|--------|--------|
| `/madrasa/ingia/` | Login |
| `/madrasa/` | Mwanzo |
| `/admin/` | Django admin |
| `/` | Health ping |

## Settings / mazingira

`DJANGO_SETTINGS_MODULE` inabaki `madrasa_sys.settings`.

| `DJANGO_ENV` | Module | Matumizi |
|--------------|--------|----------|
| `development` (default) | `madrasa_sys.settings.development` | Lab / `runserver` |
| `production` | `madrasa_sys.settings.production` | Server halisi |

Nakili `.env.example` → `.env` na urekebishe. **Usicommmit `.env`.**

### Production checklist

1. Weka `DJANGO_ENV=production`
2. Weka `DJANGO_SECRET_KEY` yenye nguvu (si `django-insecure-…`)
3. Production **forces** `DEBUG=False` (hata kama `.env` ina `DJANGO_DEBUG=True`)
4. Weka `DJANGO_ALLOWED_HOSTS` (si `*`) na `DJANGO_CSRF_TRUSTED_ORIGINS` (`https://…`)
5. Tengeneza `DJANGO_SECRET_KEY` ndefu (≥50 chars, random). `check --deploy` itaonya ikiwa fupi.
6. Endesha:

```bash
py manage.py check --deploy
py manage.py collectstatic
```

`STATIC_ROOT` ni `staticfiles/` chini ya mradi (portable). Web server lazima ihudumie `media/` nje ya `DEBUG`.

SQLite inaendelea kuwa default ya lab. Production DB (Postgres n.k.) bado haijaunganishwa katika slice hii — badilisha `DB_*` baadaye ukiwa tayari.

## Majukumu (AuthZ)

Angalia [docs/ROLES.md](docs/ROLES.md) — matrix ya Mwalimu Mkuu / Kawaida / Jaji / ofisi.

## Mawasiliano / WhatsApp (M-011)

Ofisi: `/madrasa/mawasiliano/` na **Tuma WhatsApp** (`/madrasa/mawasiliano/whatsapp/`).
Hutumia `https://wa.me/…` tu (WhatsApp ya kawaida) — **hakuna** Business API wala kutuma kiotomatiki; opereta anathibitisha Send.

## Data integrity (M-003)

- Mahudhurio: unique kwa `(mwanafunzi, tarehe, aina_ya_rekodi)` — rekodi moja kwa siku/aina.
- Matokeo: unique kwa `(mtihani, mwanafunzi)`.
- Namba ya usajili `MR-###` inatolewa atomically (na retry ikigongana).
- Migration `0011_integrity_constraints` inasafisha duplicates zilizokuwepo kabla ya kuweka constraint.

## Token API / DRF

Hakuna domain REST API. `/api-token-auth/` **imezimwa kwa default** — weka `DJANGO_ENABLE_TOKEN_AUTH=True` lab pekee. Sera: [docs/API.md](docs/API.md). Dead-code: [docs/DEAD_CODE.md](docs/DEAD_CODE.md).

## Majukumu ya kawaida

```bash
py manage.py createsuperuser
py manage.py check
py manage.py test usimamizi
```

Critical-path tests (`usimamizi/tests/`): auth, attendance, marks, fees, AuthZ, middleware, integrity, forms, dashboard, academic year/term, API token gate.

## Muundo

- `madrasa_sys/` — project (settings package, urls, wsgi)
- `usimamizi/` — app ya biashara (models, views/, templates, static, tests/)
- `docs/` — ROLES.md, ACADEMIC_YEAR.md, API.md, DEAD_CODE.md
