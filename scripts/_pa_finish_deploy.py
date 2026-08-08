"""Finish PA deploy: fix path, sanitize git remote, upload code zip + setup script."""

from __future__ import annotations

import io
import secrets
import time
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "deploy" / "pythonanywhere" / "secrets.env"
WSGI_SRC = ROOT / "deploy" / "pythonanywhere" / "wsgi.py"
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".cursor",
    "node_modules",
    ".pytest_cache",
    "htmlcov",
    "media",
    "staticfiles",
}
SKIP_FILES = {"db.sqlite3", "secrets.env", ".env"}


def load_env(path: Path) -> dict:
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def build_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if any(part.startswith(".") and part not in {".github"} for part in rel.parts[:-1]):
                continue
            if rel.name in SKIP_FILES or rel.name.endswith(".pyc"):
                continue
            if rel.as_posix() == "deploy/pythonanywhere/secrets.env":
                continue
            zf.write(path, rel.as_posix())
    return buf.getvalue()


SETUP_SH = r"""#!/bin/bash
set -euo pipefail
PROJECT=/home/rasulillahmadras/madrasa_sys
cd "$PROJECT"
if [ -f /tmp/madras_deploy.zip ]; then
  python3 - <<'PY'
import zipfile
from pathlib import Path
z = zipfile.ZipFile('/tmp/madras_deploy.zip')
z.extractall('/home/rasulillahmadras/madrasa_sys')
print('EXTRACT_OK', len(z.namelist()))
PY
fi
python3.13 -m venv .venv || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
echo SETUP_OK
"""


def main() -> int:
    cfg = load_env(SECRETS)
    username = cfg["PA_USERNAME"]
    token = cfg["PA_API_TOKEN"]
    domain = cfg["PA_DOMAIN"]
    project = cfg["PA_PROJECT_HOME"].rstrip("/")
    host = cfg.get("PA_HOST", "www.pythonanywhere.com")
    base = f"https://{host}/api/v0/user/{username}/"
    headers = {"Authorization": f"Token {token}"}

    r = requests.get(base + "cpu/", headers=headers, timeout=60)
    if r.status_code != 200:
        print("API token rejected:", r.status_code, r.text[:200])
        return 1
    print("API OK")

    # Sanitize git remote (no embedded tokens)
    clean_git = (
        "[core]\n"
        "\trepositoryformatversion = 0\n"
        "\tfilemode = true\n"
        "\tbare = false\n"
        "\tlogallrefupdates = true\n"
        '[remote "origin"]\n'
        "\turl = https://github.com/masoud180mohd-lab/Madras_Webapp.git\n"
        "\tfetch = +refs/heads/*:refs/remotes/origin/*\n"
    )
    r = requests.post(
        base + f"files/path{project}/.git/config",
        headers=headers,
        files={"content": clean_git.encode()},
        timeout=60,
    )
    print("git config sanitize:", r.status_code)

    print("Building zip...")
    zbytes = build_zip()
    print(f"Zip size: {len(zbytes)} bytes")
    r = requests.post(
        base + "files/path/tmp/madras_deploy.zip",
        headers=headers,
        files={"content": zbytes},
        timeout=300,
    )
    print("Upload zip:", r.status_code, r.text[:200])
    if r.status_code not in (200, 201):
        return 1

    r = requests.post(
        base + f"files/path{project}/_pa_setup.sh",
        headers=headers,
        files={"content": SETUP_SH.encode()},
        timeout=60,
    )
    print("Upload setup script:", r.status_code)

    django_secret = cfg.get("DJANGO_SECRET_KEY") or secrets.token_urlsafe(50)
    env_body = "\n".join(
        [
            "DJANGO_ENV=production",
            f"DJANGO_SECRET_KEY={django_secret}",
            f"DJANGO_ALLOWED_HOSTS={domain}",
            f"DJANGO_CSRF_TRUSTED_ORIGINS=https://{domain}",
            "DJANGO_SECURE_SSL_REDIRECT=True",
            "DJANGO_ALLOW_SQLITE=True",
            "DB_ENGINE=django.db.backends.sqlite3",
            f"DB_NAME={project}/db.sqlite3",
            "",
        ]
    )
    r = requests.post(
        base + f"files/path{project}/.env",
        headers=headers,
        files={"content": env_body.encode()},
        timeout=60,
    )
    print("Upload .env:", r.status_code)

    wsgi_text = WSGI_SRC.read_text(encoding="utf-8").replace(
        "/home/rasulillahmadras/Madras_Webapp", project
    )
    wsgi_remote = f"/var/www/{username}_pythonanywhere_com_wsgi.py"
    r = requests.post(
        base + f"files/path{wsgi_remote}",
        headers=headers,
        files={"content": wsgi_text.encode()},
        timeout=60,
    )
    print("Upload WSGI:", r.status_code)

    # Try existing consoles
    r = requests.get(base + "consoles/", headers=headers, timeout=60)
    consoles = r.json() if r.status_code == 200 else []
    print("Consoles:", [c.get("id") for c in consoles])

    ran = False
    for c in consoles:
        cid = c["id"]
        cmd = f"bash {project}/_pa_setup.sh\n"
        rr = requests.post(
            base + f"consoles/{cid}/send/",
            headers=headers,
            data={"input": cmd},
            timeout=60,
        )
        print(f"Send to console {cid}:", rr.status_code, rr.text[:120])
        if rr.status_code == 200:
            ran = True
            print("Waiting for setup (pip may take several minutes)...")
            for i in range(36):
                time.sleep(10)
                out = requests.get(
                    base + f"consoles/{cid}/get_latest_output/",
                    headers=headers,
                    timeout=60,
                )
                text = out.text if out.status_code == 200 else ""
                if "SETUP_OK" in text:
                    print("Setup finished OK")
                    break
                if "Traceback" in text or "ERROR" in text:
                    print("Setup may have errors; last output tail:")
                    print(text[-800:])
                    break
                if i % 3 == 2:
                    print(f"  still running... ({(i+1)*10}s)")
            else:
                print("Timed out waiting; check console output manually.")
                print(text[-800:] if text else "")
            break

    if not ran:
        # Schedule a one-time-ish daily task as fallback (user can delete later)
        r = requests.get(base + "schedule/", headers=headers, timeout=60)
        print("Existing schedules:", r.status_code, r.text[:400])
        r = requests.post(
            base + "schedule/",
            headers=headers,
            data={
                "command": f"bash {project}/_pa_setup.sh",
                "enabled": "true",
                "interval": "daily",
                "hour": "3",
                "minute": "0",
                "description": "madras one-shot setup (disable after)",
            },
            timeout=60,
        )
        print("Create schedule:", r.status_code, r.text[:300])
        print(
            "\nACTION NEEDED: Open Bash console in PA browser, then re-run:\n"
            f"  py scripts/_pa_finish_deploy.py\n"
            "Or paste:\n"
            f"  bash {project}/_pa_setup.sh"
        )

    # Patch webapp only if venv exists after setup
    r = requests.get(base + f"files/path{project}/.venv/", headers=headers, timeout=60)
    venv_ok = r.status_code == 200
    print("venv present:", venv_ok)
    patch = {
        "source_directory": project,
        "force_https": "true",
    }
    if venv_ok:
        patch["virtualenv_path"] = f"{project}/.venv"
    r = requests.patch(
        base + f"webapps/{domain}/",
        headers=headers,
        data=patch,
        timeout=60,
    )
    print("PATCH webapp:", r.status_code, r.text[:250])

    # Static mappings — keep /static/ only; /media/ goes through Django (login).
    r = requests.get(base + f"webapps/{domain}/static_files/", headers=headers, timeout=60)
    existing = r.json() if r.status_code == 200 else []
    for m in existing:
        if m.get("url") == "/media/":
            mid = m.get("id")
            if mid is not None:
                dr = requests.delete(
                    base + f"webapps/{domain}/static_files/{mid}/",
                    headers=headers,
                    timeout=60,
                )
                print(f"Removed public /media/ map id={mid}:", dr.status_code)
    wanted = {
        "/static/": f"{project}/staticfiles",
    }
    have = {m.get("url"): m for m in existing if m.get("url") != "/media/"}
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
        print(f"Static {url}:", rr.status_code)

    r = requests.post(base + f"webapps/{domain}/reload/", headers=headers, timeout=120)
    print("Reload:", r.status_code)
    print(f"Site: https://{domain}/madrasa/ingia/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
