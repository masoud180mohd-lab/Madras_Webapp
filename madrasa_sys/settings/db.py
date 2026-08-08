"""Build Django DATABASES['default'] from env (SQLite lab / Postgres prod)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import unquote, urlparse


def _sqlite_default(base_dir: Path) -> Dict[str, Any]:
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DB_NAME", str(base_dir / "db.sqlite3")),
    }


def parse_database_url(url: str) -> Dict[str, Any]:
    """
    Parse postgres:// or postgresql:// URL into a Django DATABASES entry.
    Raises ValueError for unsupported schemes.
    """
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()
    if scheme in {"postgres", "postgresql"}:
        engine = "django.db.backends.postgresql"
    elif scheme == "sqlite":
        # sqlite:///absolute/or/relative/path
        name = unquote(parsed.path or "")
        if name.startswith("/") and len(name) > 1 and os.name == "nt":
            # urlparse may yield /C:/... on Windows file URLs
            pass
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": name or ":memory:",
        }
    else:
        raise ValueError(
            f"Unsupported DATABASE_URL scheme {scheme!r}; "
            "use postgres:// or postgresql://"
        )

    name = unquote((parsed.path or "").lstrip("/"))
    config: Dict[str, Any] = {
        "ENGINE": engine,
        "NAME": name,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
    }
    return config


def build_databases(
    base_dir: Path,
    environ: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Return DATABASES mapping.

    Priority:
      1. DATABASE_URL
      2. DB_ENGINE (+ DB_NAME/USER/PASSWORD/HOST/PORT)
      3. SQLite under base_dir/db.sqlite3
    """
    env = environ if environ is not None else os.environ
    conn_max_age = int(env.get("DB_CONN_MAX_AGE", "60") or "60")

    url = (env.get("DATABASE_URL") or "").strip()
    if url:
        config = parse_database_url(url)
    else:
        engine = (env.get("DB_ENGINE") or "").strip()
        if not engine or engine.endswith("sqlite3"):
            config = _sqlite_default(base_dir)
            if engine:
                config["ENGINE"] = engine
            if env.get("DB_NAME"):
                config["NAME"] = env["DB_NAME"]
        else:
            config = {
                "ENGINE": engine,
                "NAME": env.get("DB_NAME", ""),
                "USER": env.get("DB_USER", ""),
                "PASSWORD": env.get("DB_PASSWORD", ""),
                "HOST": env.get("DB_HOST", ""),
                "PORT": env.get("DB_PORT", ""),
            }

    if config["ENGINE"] != "django.db.backends.sqlite3":
        config["CONN_MAX_AGE"] = conn_max_age
        config.setdefault("OPTIONS", {})

    return {"default": config}
