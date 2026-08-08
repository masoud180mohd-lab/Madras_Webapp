# Deploy kwenye PythonAnywhere

**Akaunti yako:** `rasulillahmadras`  
**Tovuti:** https://rasulillahmadras.pythonanywhere.com/madrasa/

**VPS** = server ya Linux unayoikodisha wewe mwenyewe (Nginx + Gunicorn).  
**PythonAnywhere** = hosting tayari — wewe huhitaji VPS. App yako inaendesha hapa.

## Kwa mwenye hafahamu — mpango A (bure: SQLite)

Akaunti ya **free** haina MySQL. Tunatumia **SQLite** + `DJANGO_ALLOW_SQLITE=True`.

Mimi (agent) **siwezi** kuingia bila ruhusa. Fanya hivi **mara moja**, kisha andika *tayari*:

1. Ingia [pythonanywhere.com](https://www.pythonanywhere.com/) → **Account** → **API token** → Create / copy.
2. Fungua faili `deploy/pythonanywhere/secrets.env` kwenye Cursor.
3. Bandika: `PA_API_TOKEN=token-yako` (acha `DB_MODE=sqlite`).
4. **Usitume token kwenye chat** — andika tu **tayari**.

Halafu nitaendesha `py scripts/pa_configure.py` (`.env`, WSGI, static/media, reload).

**Backup:** nakili `db.sqlite3` na folder `media/` mara kwa mara (Files tab).

Lab (PC yako) inaweza kubaki SQLite. **Kwenye PythonAnywhere usitumie SQLite** kwa data ya kweli — tumia **MySQL** (mpango wa kawaida wa PA) au Postgres ukiwa na mpango unaounga mkono.

## 1. Weka mradi

1. Git clone au upload `Madras_Webapp` ndani ya home yako, mfano:  
   `/home/JINA_LAKO/Madras_Webapp`
2. Consoles → Bash:
   ```bash
   cd ~/Madras_Webapp
   python3.10 -m venv .venv
   source .venv/bin/activate
   pip install -U pip
   pip install -r requirements.txt
   ```
   (Chagua Python version inayolingana na Web tab — 3.10 au 3.11 kawaida.)

## 2. Unda MySQL (Databases tab)

1. PythonAnywhere → **Databases**
2. Weka MySQL password (ihifadhi salama)
3. Create database, jina mfano: `JINA_LAKO$madrasa`
4. Andika host: mara nyingi `JINA_LAKO.mysql.pythonanywhere-services.com`

## 3. Faili `.env` (production)

Katika `~/Madras_Webapp/.env`:

```env
DJANGO_ENV=production
DJANGO_SECRET_KEY=weka-key-ndefu-random
DJANGO_ALLOWED_HOSTS=JINA_LAKO.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://JINA_LAKO.pythonanywhere.com
DJANGO_SECURE_SSL_REDIRECT=True

DB_ENGINE=django.db.backends.mysql
DB_NAME=JINA_LAKO$madrasa
DB_USER=JINA_LAKO
DB_PASSWORD=mysql-password-yako
DB_HOST=JINA_LAKO.mysql.pythonanywhere-services.com
DB_PORT=3306
```

Tengeneza secret:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 4. Migrate + static + superuser

```bash
cd ~/Madras_Webapp
source .venv/bin/activate
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 5. Web app + WSGI

1. **Web** → Add a new web app → Manual configuration → Python 3.10/3.11  
2. Source code: `/home/JINA_LAKO/Madras_Webapp`  
3. Virtualenv: `/home/JINA_LAKO/Madras_Webapp/.venv`  
4. Fungua **WSGI configuration file** — badilisha kuwa kama hii (rekebisha njia/jina):

```python
import os
import sys

project_home = "/home/JINA_LAKO/Madras_Webapp"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "madrasa_sys.settings")
# DJANGO_ENV na DB_* zinakuja kutoka .env (load_dotenv ndani ya settings)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

5. **Static files** (Web tab):

| URL            | Directory                                      |
|----------------|------------------------------------------------|
| `/static/`     | `/home/JINA_LAKO/Madras_Webapp/staticfiles`    |

**Usiongeze** mapping ya `/media/` → folder `media`. Picha/nyenzo zinapitia Django (`protected_media`) — **login inahitajika**. Mapping ya umma inafungua picha bila kuingia.

Ikiwa `/media/` ilikuwa imewekwa zamani: Web tab → Static files → **futa** mstari wa `/media/`, kisha Reload. (Script `pa_configure.py` pia inajaribu kuiondoa.)

6. Bonyeza **Reload**.

## 6. Angalia app

- `https://JINA_LAKO.pythonanywhere.com/madrasa/ingia/`
- Login, jaribu malipo, mawasiliano, upload picha

Ikiwa error: Web → **Log files** (error / server log).

## 7. Sasisha baada ya `git pull`

```bash
cd ~/Madras_Webapp
source .venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Kisha **Reload** kwenye Web tab.

## 8. Backup (muhimu)

- Databases tab / `mysqldump` ya MySQL yako  
- Nakili folder `media/` (picha za wanafunzi)

## Matatizo ya kawaida

| Tatizo | Suluhisho |
|--------|-----------|
| DisallowedHost | `DJANGO_ALLOWED_HOSTS` = jina kamili la PA |
| CSRF failed | `DJANGO_CSRF_TRUSTED_ORIGINS=https://JINA_LAKO.pythonanywhere.com` |
| Static haionekani | `collectstatic` + mapping `/static/` → `staticfiles` |
| DB connection refused | Host/user/password kutoka Databases tab; jina la DB lina `$` |
| SQLite “disk I/O” | Weka MySQL — usitumie `db.sqlite3` kwenye PA |

## VPS vs PythonAnywhere

| | PythonAnywhere | VPS ([DEPLOY.md](DEPLOY.md)) |
|--|----------------|------------------------------|
| Unahitaji nini | Akaunti ya PA | Server Ubuntu + DNS |
| Database | MySQL (kawaida) | Postgres |
| Web server | PA inasimamia | Nginx + Gunicorn wewe |
| Kwa nani | Rahisi kuanza | Udhibiti kamili |

Wewe uko upande wa **PythonAnywhere** — fuata faili hii, si setup ya VPS.
