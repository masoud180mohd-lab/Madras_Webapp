"""
Local / lab settings. SQLite stays the default database.
"""

from .base import *  # noqa: F403
from .base import env_bool, env_list
import os

DEBUG = env_bool("DJANGO_DEBUG", True)

# Lab-only fallback. Never use this value in production (see production.py).
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-me-madrasatul-rasulillah",
)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1", "[::1]", "*"])

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
)

# Optional LAN origin from .env (comma-separated) merges above via env override.
