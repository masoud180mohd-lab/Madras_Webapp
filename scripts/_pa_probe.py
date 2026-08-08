import requests
from pathlib import Path


def load_env(path):
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


cfg = load_env(Path("deploy/pythonanywhere/secrets.env"))
u, t = cfg["PA_USERNAME"], cfg["PA_API_TOKEN"]
base = f"https://{cfg.get('PA_HOST', 'www.pythonanywhere.com')}/api/v0/user/{u}/"
h = {"Authorization": f"Token {t}"}
for path in [
    f"/home/{u}/",
    f"/home/{u}/Madras_Webapp/",
    f"/home/{u}/mysite/",
    "/var/www/",
]:
    r = requests.get(base + "files/tree/", params={"path": path}, headers=h, timeout=60)
    print("===", path, r.status_code, "n=", len(r.json()) if r.status_code == 200 else r.text[:120])
    if r.status_code == 200:
        for p in r.json()[:40]:
            print(" ", p)

r = requests.get(base + f"webapps/{cfg['PA_DOMAIN']}/", headers=h, timeout=60)
print("WEBAPP", r.status_code)
print(r.text[:1200])
