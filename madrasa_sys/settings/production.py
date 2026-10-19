"""
Production settings. Requires environment variables; fails closed.
"""

import os
import socket

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import MIDDLEWARE, env_bool, env_list

DEBUG = False
# Intentionally ignore DJANGO_DEBUG in production so a shared .env cannot reopen debug.

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY.startswith("django-insecure"):
    raise ImproperlyConfigured(
        "Set a strong DJANGO_SECRET_KEY in the environment for production."
    )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["*"]:
    raise ImproperlyConfigured(
        "Set DJANGO_ALLOWED_HOSTS to explicit hostnames (not '*') for production."
    )

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured(
        "Set DJANGO_CSRF_TRUSTED_ORIGINS (https://your-domain) for production."
    )

# Render's Blueprint `fromService: property: host` injects the bare internal service
# name (`madrasa-webapp`) without `.onrender.com`, while public traffic and health
# checks use `<service>.onrender.com` or internal container IPs. Ensure Render hosts
# are always trusted when running on Render.
_render_ext_host = (os.environ.get("RENDER_EXTERNAL_HOSTNAME") or "").strip()
_is_render = bool(
    os.environ.get("RENDER")
    or _render_ext_host
    or os.environ.get("RENDER_DB_REGION")
    or any("onrender.com" in h or h == "madrasa-webapp" for h in ALLOWED_HOSTS + CSRF_TRUSTED_ORIGINS)
)
if _is_render:
    for _extra_host in (
        _render_ext_host,
        "rasulillah.me",
        "www.rasulillah.me",
        ".rasulillah.me",
        "madrasa-webapp.onrender.com",
        ".onrender.com",
        "localhost",
        "127.0.0.1",
    ):
        if _extra_host and _extra_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(_extra_host)
    try:
        for _ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if _ip and _ip not in ALLOWED_HOSTS:
                ALLOWED_HOSTS.append(_ip)
    except OSError:
        pass
    for _extra_origin in (
        f"https://{_render_ext_host}" if _render_ext_host else "",
        "https://rasulillah.me",
        "https://www.rasulillah.me",
        "https://madrasa-webapp.onrender.com",
        "https://*.onrender.com",
    ):
        if _extra_origin and _extra_origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(_extra_origin)

_db_engine = DATABASES["default"].get("ENGINE", "")  # noqa: F405
_allow_sqlite = env_bool("DJANGO_ALLOW_SQLITE", False)
_allowed_engines = {
    "django.db.backends.postgresql",
    "django.db.backends.mysql",
}
if _db_engine.endswith("sqlite3"):
    if not _allow_sqlite:
        raise ImproperlyConfigured(
            "Production SQLite is off by default. For PythonAnywhere free set "
            "DJANGO_ALLOW_SQLITE=True (see docs/DEPLOY_PYTHONANYWHERE.md). "
            "Prefer MySQL (paid PA) or Postgres (VPS) when you can."
        )
elif _db_engine not in _allowed_engines:
    raise ImproperlyConfigured(
        f"Unsupported production DB engine {_db_engine!r}. "
        "Use postgresql, mysql, or sqlite with DJANGO_ALLOW_SQLITE=True."
    )

# WhiteNoise: serve collected static files from Gunicorn when Nginx is not aliasing them.
# RenderHealthCheckMiddleware runs before SecurityMiddleware so internal 10.x.x.x probes pass.
MIDDLEWARE = [
    "usimamizi.middleware.RenderHealthCheckMiddleware",
    MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]
# Cloudinary is opt-in. When credentials are present, new uploads go to Cloudinary
# through the protected /media/ backend (usimamizi.storage.ProtectedCloudinaryStorage),
# which keeps field.url pointing at the authenticated endpoint instead of the public
# CDN. When they are absent, production stays on local FileSystemStorage. Detected
# from the environment directly so settings never import the usimamizi app at load
# time; the backend is referenced by dotted string path so Django imports it lazily.
# Mirrors usimamizi.cloudinary_utils.is_cloudinary_enabled (CLOUDINARY_URL, or the
# discrete CLOUDINARY_CLOUD_NAME + API_KEY + API_SECRET trio that Render provides).
_cloudinary_keys = ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
cloudinary_ready = bool(
    os.environ.get("CLOUDINARY_URL")
    or all(os.environ.get(key) for key in _cloudinary_keys)
)

STORAGES = {
    "default": {
        "BACKEND": (
            "usimamizi.storage.ProtectedCloudinaryStorage"
            if cloudinary_ready
            else "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
