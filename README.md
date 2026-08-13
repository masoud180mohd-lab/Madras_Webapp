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

### Production / hosting

- Lab: SQLite (`db.sqlite3`).
- Production **inakataa SQLite**.
- **PythonAnywhere:** free = SQLite (`DJANGO_ALLOW_SQLITE=True`); paid = MySQL — **[docs/DEPLOY_PYTHONANYWHERE.md](docs/DEPLOY_PYTHONANYWHERE.md)**.
- **VPS** (server yako): Postgres + Nginx — [docs/DEPLOY.md](docs/DEPLOY.md).

```bash
py manage.py check --deploy
py manage.py collectstatic
```

## Majukumu (AuthZ)

Angalia [docs/ROLES.md](docs/ROLES.md) — matrix ya Mwalimu Mkuu / Kawaida / Jaji / ofisi.

## Mawasiliano / WhatsApp (M-011)

Ofisi: `/madrasa/mawasiliano/` na **Tuma WhatsApp** (`/madrasa/mawasiliano/whatsapp/`).
Hutumia `https://wa.me/…` tu (WhatsApp ya kawaida) — **hakuna** Business API wala kutuma kiotomatiki; opereta anathibitisha Send.
Kila mwanafunzi anaweza kuwa na **mzazi wa kwanza + wa pili** (mf. Baba + Mama): jina, uhusiano, namba.

## Dashboard / ufuatiliaji

Mwanzo huonyesha vipimo + orodha fupi ya **deni la ada** na **mahudhurio** (hawapo leo / watoro wiki) kwa ruhusa husika — ufuatiliaji wa ofisi, si push notifications.

## Usalama wa media

`/media/...` (picha, nyenzo) inahudumiwa na Django **baada ya login** tu — si static ya umma. Kwenye PythonAnywhere **usiongeze** Static files mapping ya `/media/`.

## Ada kwa mwaka / mwezi

Aina za ada zinaweza kufungwa na **mwaka wa masomo** (+ mwezi hiari). Lebo: `Ada · Aprili · 2025/2026` — haitachanganyika na Aprili ya mwaka mwingine. Mapato → Aina za Ada; Malipo huchuja kwa mwaka hai.

## Simu / majedwali

Kwenye skrini ≤768px, majedwali ya `.app-table` / `.data-table` yanakuwa **kadi** (si scroll ya upande). Spreadsheet/alama: weka `table-keep-scroll` au tumia `.marks-table`.

## Hamisha darasa (M-012)

Mkuu: `/madrasa/hamisha-darasa/` — uhamisho wa wanafunzi darasa → darasa (mwisho wa mwaka) kwa kuthibitisha; inaandika ukaguzi. Maelezo: [docs/ACADEMIC_YEAR.md](docs/ACADEMIC_YEAR.md).

## Data integrity (M-003)

- Mahudhurio: unique kwa `(mwanafunzi, tarehe, aina_ya_rekodi)` — rekodi moja kwa siku/aina.
- Matokeo: unique kwa `(mtihani, mwanafunzi)`.
- Namba ya usajili `MR-###` inatolewa atomically (na retry ikigongana).
- Migration `0011_integrity_constraints` inasafisha duplicates zilizokuwepo kabla ya kuweka constraint.

## Token API / DRF

Staff mobile API: `/api/v1/` (JWT). Sera na endpoints: [docs/API.md](docs/API.md).

`/api-token-auth/` **imezimwa kwa default** (legacy) — weka `DJANGO_ENABLE_TOKEN_AUTH=True` lab pekee. Dead-code: [docs/DEAD_CODE.md](docs/DEAD_CODE.md).

## Majukumu ya kawaida

```bash
py manage.py createsuperuser
py manage.py check
py manage.py test usimamizi
```

Critical-path tests (`usimamizi/tests/`): auth, attendance, marks, fees, AuthZ, middleware, integrity, forms, dashboard, academic year/term, API token gate, `/api/v1/` JWT.

## Muundo

- `madrasa_sys/` — project (settings package, urls, wsgi)
- `usimamizi/` — app ya biashara (models, views/, templates, static, tests/)
- `docs/` — ROLES.md, ACADEMIC_YEAR.md, API.md, DEAD_CODE.md
