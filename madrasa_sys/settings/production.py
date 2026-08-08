"""
Production settings. Requires environment variables; fails closed.
"""

import os

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

_db_engine = DATABASES["default"].get("ENGINE", "")  # noqa: F405
if _db_engine.endswith("sqlite3"):
    raise ImproperlyConfigured(
        "Production must not use SQLite. On PythonAnywhere use MySQL "
        "(DB_ENGINE=django.db.backends.mysql); on a VPS use Postgres. "
        "See docs/DEPLOY_PYTHONANYWHERE.md or docs/DEPLOY.md."
    )
_allowed_engines = {
    "django.db.backends.postgresql",
    "django.db.backends.mysql",
}
if _db_engine not in _allowed_engines:
    raise ImproperlyConfigured(
        f"Unsupported production DB engine {_db_engine!r}. "
        "Use postgresql or mysql."
    )

# WhiteNoise: serve collected static files from Gunicorn when Nginx is not aliasing them.
MIDDLEWARE = [
    MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
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
