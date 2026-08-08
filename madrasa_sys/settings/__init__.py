"""
Load settings module from DJANGO_ENV (default: development).

Usage:
  DJANGO_ENV=development  -> madrasa_sys.settings.development
  DJANGO_ENV=production   -> madrasa_sys.settings.production

DJANGO_SETTINGS_MODULE stays "madrasa_sys.settings".
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(_BASE_DIR / ".env")

_env = os.environ.get("DJANGO_ENV", "development").strip().lower()

if _env == "production":
    from .production import *  # noqa: F403
elif _env in {"development", "dev", "local"}:
    from .development import *  # noqa: F403
else:
    raise ImportError(
        "Unknown DJANGO_ENV=%r. Use 'development' or 'production'." % (_env,)
    )
