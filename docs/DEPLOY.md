# Deploy — Ubuntu VPS + Postgres + Nginx + Gunicorn

Target stack for **Al-Madrasatul Rasulillah** MIS (Django SSR, `media/` uploads).
Lab stays on SQLite; **production must use Postgres** (`madrasa_sys.settings.production` rejects SQLite).

See also: [ROLES.md](ROLES.md), [API.md](API.md), [`.env.example`](../.env.example).

## 0. Before you start

- Domain DNS A/AAAA → VPS IP
- Ubuntu 22.04+ VPS with sudo
- Repo cloned (e.g. `/srv/madrasa/Madras_Webapp`)
- Do **not** put `db.sqlite3` on a public host

## 1. System packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx postgresql postgresql-contrib certbot python3-certbot-nginx
```

## 2. Postgres database + role

```bash
sudo -u postgres psql <<'SQL'
CREATE USER madrasa WITH PASSWORD 'REPLACE_STRONG_PASSWORD';
CREATE DATABASE madrasa OWNER madrasa;
GRANT ALL PRIVILEGES ON DATABASE madrasa TO madrasa;
SQL
```

On Postgres 15+, also grant schema rights inside the DB:

```bash
sudo -u postgres psql -d madrasa -c "GRANT ALL ON SCHEMA public TO madrasa;"
```

## 3. App user + venv

```bash
sudo useradd --system --home /srv/madrasa --shell /bin/bash madrasa || true
sudo mkdir -p /srv/madrasa
sudo chown -R madrasa:madrasa /srv/madrasa
# clone or pull as madrasa user into /srv/madrasa/Madras_Webapp
cd /srv/madrasa/Madras_Webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 4. Production `.env`

```bash
cp .env.example .env
# edit .env — never commit it
```

Minimum:

```env
DJANGO_ENV=production
DJANGO_SECRET_KEY=<long random — py -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DJANGO_ALLOWED_HOSTS=madras.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://madras.example.com
DJANGO_SECURE_SSL_REDIRECT=True

DB_ENGINE=django.db.backends.postgresql
DB_NAME=madrasa
DB_USER=madrasa
DB_PASSWORD=REPLACE_STRONG_PASSWORD
DB_HOST=127.0.0.1
DB_PORT=5432
# Or: DATABASE_URL=postgres://madrasa:REPLACE_STRONG_PASSWORD@127.0.0.1:5432/madrasa
```

## 5. Migrate, static, superuser

```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)   # or use dotenv already loaded by settings
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Ensure writable dirs:

```bash
mkdir -p media staticfiles
# ownership: madrasa user must write media/
```

## 6. Gunicorn (systemd)

`/etc/systemd/system/madrasa.service`:

```ini
[Unit]
Description=Madras Gunicorn
After=network.target postgresql.service

[Service]
User=madrasa
Group=madrasa
WorkingDirectory=/srv/madrasa/Madras_Webapp
EnvironmentFile=/srv/madrasa/Madras_Webapp/.env
ExecStart=/srv/madrasa/Madras_Webapp/.venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/madrasa/gunicorn.sock \
    madrasa_sys.wsgi:application
RuntimeDirectory=madrasa
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now madrasa
sudo systemctl status madrasa
```

## 7. Nginx

`/etc/nginx/sites-available/madrasa`:

```nginx
server {
    listen 80;
    server_name madras.example.com;

    client_max_body_size 12M;

    location /static/ {
        alias /srv/madrasa/Madras_Webapp/staticfiles/;
    }

    location /media/ {
        alias /srv/madrasa/Madras_Webapp/media/;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/madrasa/gunicorn.sock;
    }
}
```

```bash
sudo ln -sf /etc/nginx/sites-available/madrasa /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

WhiteNoise is enabled in production settings as a fallback for static files; prefer Nginx `alias` for `/static/` and `/media/`.

## 8. TLS (Certbot)

```bash
sudo certbot --nginx -d madras.example.com
```

Confirm `DJANGO_CSRF_TRUSTED_ORIGINS` uses `https://…` and `SECURE_SSL_REDIRECT=True`.

## 9. Backups

Daily (example cron as root or backup user):

```bash
# Postgres
0 2 * * * sudo -u postgres pg_dump madrasa | gzip > /var/backups/madrasa/db-$(date +\%F).sql.gz
# Media
30 2 * * * tar -czf /var/backups/madrasa/media-$(date +\%F).tgz -C /srv/madrasa/Madras_Webapp media
```

Keep ≥7 days; test restore once.

## 10. Smoke checklist

- [ ] `https://madras.example.com/madrasa/ingia/` loads (HTTPS)
- [ ] Login as Mkuu / ofisi
- [ ] Malipo: record a payment + risiti PDF
- [ ] Mawasiliano + WhatsApp link opens `wa.me`
- [ ] Upload student photo → file under `media/`
- [ ] `python manage.py check --deploy` clean (or only known warnings)

## Lab → production data

Prefer **fresh production** + recreate staff users and critical masters (madarasa, aina za ada).

For a small lab dump only:

```bash
# on lab
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission -e sessions \
  -o lab-dump.json
# on prod (after migrate, carefully)
python manage.py loaddata lab-dump.json
```

Media files must be copied separately (`rsync media/`). Large messy dumps often fail — fix conflicts manually.

## Updates (redeploy)

```bash
cd /srv/madrasa/Madras_Webapp
source .venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart madrasa
```
