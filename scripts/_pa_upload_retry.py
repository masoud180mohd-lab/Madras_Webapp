"""Retry PA file uploads with throttle backoff. Skips static/admin (collectstatic)."""

from __future__ import annotations

import time
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "deploy" / "pythonanywhere" / "secrets.env"
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
    "static",  # vendored; collectstatic fills staticfiles
}
SKIP_FILES = {"db.sqlite3", "secrets.env", ".env"}


def main() -> int:
    cfg = dotenv_values(SECRETS)
    u, t = cfg["PA_USERNAME"], cfg["PA_API_TOKEN"]
    headers = {"Authorization": f"Token {t}"}
    base = f"https://{cfg.get('PA_HOST', 'www.pythonanywhere.com')}/api/v0/user/{u}/"
    project = cfg["PA_PROJECT_HOME"].rstrip("/")

    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(p in SKIP_DIRS for p in rel.parts):
            continue
        if any(p.startswith(".") and p not in {".github"} for p in rel.parts[:-1]):
            continue
        if rel.name in SKIP_FILES or rel.name.endswith(".pyc"):
            continue
        if rel.as_posix() == "deploy/pythonanywhere/secrets.env":
            continue
        files.append(rel)

    print(f"Uploading {len(files)} files (with backoff)...")
    ok = fail = 0
    for i, rel in enumerate(files, 1):
        remote = f"{project}/{rel.as_posix()}"
        content = (ROOT / rel).read_bytes()
        for attempt in range(6):
            rr = requests.post(
                base + f"files/path{remote}",
                headers=headers,
                files={"content": content},
                timeout=120,
            )
            if rr.status_code in (200, 201):
                ok += 1
                break
            if rr.status_code == 429:
                wait = 30
                try:
                    wait = int(rr.json().get("detail", "").split()[-2]) + 2
                except Exception:
                    pass
                print(f"  throttle, sleep {wait}s ({rel})")
                time.sleep(max(wait, 5))
                continue
            print("FAIL", remote, rr.status_code, rr.text[:120])
            fail += 1
            break
        else:
            fail += 1
            print("FAIL after retries", remote)
        if i % 25 == 0:
            print(f"  progress {i}/{len(files)} ok={ok} fail={fail}")
            time.sleep(1)
    print("DONE ok", ok, "fail", fail)

    checks = [
        "requirements.txt",
        "usimamizi/views/contacts.py",
        "usimamizi/migrations/0019_hamisha_darasa_audit.py",
        "usimamizi/templates/usimamizi/orodha_wanafunzi.html",
        "madrasa_sys/settings/production.py",
    ]
    for p in checks:
        rr = requests.get(base + f"files/path{project}/{p}", headers=headers, timeout=60)
        print("check", p, rr.status_code)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
