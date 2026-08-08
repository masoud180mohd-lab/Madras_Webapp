"""
Configure rasulillahmadras.pythonanywhere.com via API after secrets.env exists.

Usage (from repo root, after filling deploy/pythonanywhere/secrets.env):
  py -m pip install requests
  py scripts/pa_configure.py
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: py -m pip install requests")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "deploy" / "pythonanywhere" / "secrets.env"
WSGI_SRC = ROOT / "deploy" / "pythonanywhere" / "wsgi.py"


def load_env(path: Path) -> dict:
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def main() -> int:
    if not SECRETS.exists():
        print(
            f"Missing {SECRETS}\n"
            "1) Copy .env.pythonanywhere.example → deploy/pythonanywhere/secrets.env\n"
            "2) Fill PA_API_TOKEN and DB_PASSWORD\n"
            "3) Run this script again."
        )
        return 1

    cfg = load_env(SECRETS)
    required = [
        "PA_USERNAME",
        "PA_API_TOKEN",
        "DB_PASSWORD",
        "DB_NAME",
        "DB_USER",
        "DB_HOST",
        "PA_PROJECT_HOME",
        "PA_DOMAIN",
    ]
    missing = [k for k in required if not cfg.get(k) or "bandika" in cfg.get(k, "")]
    if missing:
        print("Fill these in secrets.env:", ", ".join(missing))
        return 1

    username = cfg["PA_USERNAME"]
    host = cfg.get("PA_HOST", "www.pythonanywhere.com")
    token = cfg["PA_API_TOKEN"]
    domain = cfg["PA_DOMAIN"]
    project = cfg["PA_PROJECT_HOME"]
    base = f"https://{host}/api/v0/user/{username}/"
    headers = {"Authorization": f"Token {token}"}

    # Probe auth
    r = requests.get(base + "cpu/", headers=headers, timeout=60)
    if r.status_code != 200:
        print("API token rejected:", r.status_code, r.text[:300])
        return 1
    print("API OK — CPU quota reachable.")

    # Inspect webapps
    r = requests.get(base + "webapps/", headers=headers, timeout=60)
    r.raise_for_status()
    apps = r.json()
    print("Webapps:", [a.get("domain_name") for a in apps])

    # Build and upload .env
    django_secret = cfg.get("DJANGO_SECRET_KEY") or secrets.token_urlsafe(50)
    env_body = "\n".join(
        [
            "DJANGO_ENV=production",
            f"DJANGO_SECRET_KEY={django_secret}",
            f"DJANGO_ALLOWED_HOSTS={domain}",
            f"DJANGO_CSRF_TRUSTED_ORIGINS=https://{domain}",
            "DJANGO_SECURE_SSL_REDIRECT=True",
            "DB_ENGINE=django.db.backends.mysql",
            f"DB_NAME={cfg['DB_NAME']}",
            f"DB_USER={cfg['DB_USER']}",
            f"DB_PASSWORD={cfg['DB_PASSWORD']}",
            f"DB_HOST={cfg['DB_HOST']}",
            "DB_PORT=3306",
            "",
        ]
    )
    env_path = f"{project}/.env"
    r = requests.post(
        base + f"files/path{env_path}",
        headers=headers,
        files={"content": env_body.encode("utf-8")},
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print("Failed to upload .env:", r.status_code, r.text[:400])
        return 1
    print(f"Uploaded {env_path}")

    # Upload WSGI
    wsgi_remote = f"/var/www/{username}_pythonanywhere_com_wsgi.py"
    wsgi_text = WSGI_SRC.read_text(encoding="utf-8").replace(
        "/home/rasulillahmadras/Madras_Webapp", project
    )
    r = requests.post(
        base + f"files/path{wsgi_remote}",
        headers=headers,
        files={"content": wsgi_text.encode("utf-8")},
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print("Failed to upload WSGI:", r.status_code, r.text[:400])
        return 1
    print(f"Uploaded {wsgi_remote}")

    # Patch webapp paths
    r = requests.patch(
        base + f"webapps/{domain}/",
        headers=headers,
        data={
            "source_directory": project,
            "virtualenv_path": f"{project}/.venv",
            "force_https": "true",
        },
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print("Warning: could not PATCH webapp:", r.status_code, r.text[:300])
    else:
        print("Webapp source/virtualenv updated.")

    # Static mappings
    r = requests.get(base + f"webapps/{domain}/static_files/", headers=headers, timeout=60)
    existing = r.json() if r.status_code == 200 else []
    wanted = {
        "/static/": f"{project}/staticfiles",
        "/media/": f"{project}/media",
    }
    have = {m.get("url"): m for m in existing}
    for url, path in wanted.items():
        if url in have:
            mid = have[url]["id"]
            rr = requests.patch(
                base + f"webapps/{domain}/static_files/{mid}/",
                headers=headers,
                data={"url": url, "path": path},
                timeout=60,
            )
        else:
            rr = requests.post(
                base + f"webapps/{domain}/static_files/",
                headers=headers,
                data={"url": url, "path": path},
                timeout=60,
            )
        if rr.status_code not in (200, 201):
            print(f"Static mapping {url} failed:", rr.status_code, rr.text[:200])
        else:
            print(f"Static mapping OK: {url} → {path}")

    # Reload
    r = requests.post(base + f"webapps/{domain}/reload/", headers=headers, timeout=120)
    if r.status_code not in (200, 201):
        print("Reload failed:", r.status_code, r.text[:300])
        return 1
    print("Webapp reloaded.")
    print(f"Open: https://{domain}/madrasa/ingia/")
    print(
        "\nBADO UNAHITAJIKA (mara moja kwenye Bash console ya PA):\n"
        f"  cd {project}\n"
        "  source .venv/bin/activate   # au unda venv kama haipo\n"
        "  pip install -r requirements.txt\n"
        "  python manage.py migrate\n"
        "  python manage.py collectstatic --noinput\n"
        "  python manage.py createsuperuser\n"
        "Kisha Reload tena kwenye Web tab."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
