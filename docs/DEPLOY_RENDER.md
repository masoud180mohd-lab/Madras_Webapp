# Render: Uendeshaji (Operations Runbook)

Runbook hii inaeleza jinsi **Madras_Webapp** inavyoendeshwa kwenye Render **sasa**.
Kwa historia ya uhamishaji kutoka PythonAnywhere, angalia sehemu ya 6 — hatua
zile za zamani zimepitwa na wakati.

## 1. Topolojia ya sasa (tangu 2026-10-20)

| Sehemu | Thamani |
|---|---|
| Web service | `madrasa-webapp-oregon` — region **Oregon (US West)**, plan Free, imeundwa **manually** kwenye dashboard (si Blueprint) |
| Database | `madrasa-db` — region **Oregon**, inamilikiwa na Blueprint (`databases:` kwenye `render.yaml` pekee) |
| Media | Cloudinary (`CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET`) |
| Custom domain | `rasulillah.me` → A record `216.24.57.1` (Render anycast); `www.rasulillah.me` → CNAME `madrasa-webapp-oregon.onrender.com` (Namecheap) |
| Mobile app | `https://rasulillah.me` — hakuna APK rebuild inayohitajika domain ikibaki hii |

Mambo muhimu:

- Web na database ziko **region moja**, kwa hivyo `DATABASE_URL` inaweza kutumia
  hostname ya ndani `dpg-…-a` (private network). `madrasa_sys/settings/db.py`
  hurudisha external FQDN (`….oregon-postgres.render.com`) ikiwa DNS ya ndani
  ishindikane — hivyo hakuna hatari kubwa ikibadilishwa.
- Render **haiwezi kubadilisha region** wala `*.onrender.com` subdomain ya
  service iliyopo. Kubadilisha mojawapo kunahitaji kuunda service mpya.
- `render.yaml` haitangazi web service tena (service ni manual); kama
  utaitangaza, Blueprint sync inaweza kuunda service ya duplicate.

## 2. Deploy ya kila siku

1. Commit na push kwenye `main` — `autoDeploy` ipo ON.
2. Render inajenga: `./build.sh` → `manage.py check` → `migrate --noinput` →
   `collectstatic --noinput`.
3. Kufuatilia: Render → service → **Events** (build/deploy) na **Logs** (runtime).
4. Uthibitisho wa haraka baada ya deploy:
   - `https://rasulillah.me/` → `Muunganisho umefanikiwa!` (health ping)
   - `https://rasulillah.me/madrasa/` → ukurasa wa kuingia (`<html lang="sw">`)
   - `https://rasulillah.me/api/v1/mwanzo/` → `401` bila token ya JWT (sahihi)

## 3. Environment variables

Zinaishi kwenye dashboard (service → Settings → **Environment**) — si kwenye
repo. Orodha inayohitajika:

```
PYTHON_VERSION=3.12.7
RENDER_DB_REGION=oregon
DATABASE_URL=postgresql://madrasa_user:<password>@dpg-…-a/madrasa_db_njfe   # hostname ya ndani; Render huongeza suffix kwenye jina la database
DJANGO_ENV=production
DJANGO_SETTINGS_MODULE=madrasa_sys.settings
PYTHONUNBUFFERED=1
DJANGO_SECRET_KEY=<secret>
DJANGO_ALLOWED_HOSTS=rasulillah.me,www.rasulillah.me,madrasa-webapp.onrender.com,.onrender.com,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://rasulillah.me,https://www.rasulillah.me,https://madrasa-webapp.onrender.com,https://*.onrender.com
DJANGO_SECURE_SSL_REDIRECT=False
CLOUDINARY_CLOUD_NAME=<secret>
CLOUDINARY_API_KEY=<secret>
CLOUDINARY_API_SECRET=<secret>
```

Kubadilisha env variable kunachochea deploy/restart. `DJANGO_SECRET_KEY`
ikibadilishwa, watumiaji wote watalazimika kuingia tena.

## 4. Backup na restore za database

Kutoka Render Shell (au popote settings zinapopatikana):

```bash
python manage.py export_madrasa_data --output madrasa_backup.json
python manage.py import_madrasa_data --input madrasa_backup.json --migrate
```

Media haihitaji backup ya local — iko Cloudinary. Faili ya `.env`, `db.sqlite3`,
`media/`, na `staticfiles/` hazipaswi kamwe ku-commit.

## 5. Kujenga upya web service (disaster recovery)

1. Render → **New +** → **Web Service** (SI Blueprint).
2. Repo `masoud180mohd-lab/Madras_Webapp`, branch `main`, runtime Python 3.
3. Region **Oregon (US West)** — lazima ilingane na database.
4. Build: `./build.sh` · Start: `gunicorn madrasa_sys.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --max-requests 1000 --max-requests-jitter 50` · Health check: `/`
5. Weka environment variables zote za sehemu ya 3.
6. Baada ya **Live**: Settings → Custom Domains → ongeza `rasulillah.me`,
   kisha `www.rasulillah.me`. DNS ni tayari (A `216.24.57.1` na CNAME ya
   `www`), kwa hivyo uthibitisho hufanyika haraka bila kuandika DNS upya.
7. Usigusa `madrasa-db` — data zote zipo hapo.

## 6. Historia (imepitwa na wakati)

- Uhamishaji kutoka PythonAnywhere kwenda Render umekamilika;
  `docs/DEPLOY_PYTHONANYWHERE.md` ni kumbukumbu ya kihistoria tu.
- Hadi **2026-10-20** web service ilikuwa Singapore wakati database iko Oregon
  (cross-region workaround: external `DATABASE_URL` + `RENDER_DB_REGION`).
  Sasa zote ziko Oregon; mantiki ya fallback imebaki kwenye `db.py` kama kinga.
- Service ya zamani ya Singapore (`madrasa-webapp`) ilifutwa baada ya
  kuhamisha domains kwenda service ya Oregon.
