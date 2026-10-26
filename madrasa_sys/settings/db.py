"""Build Django DATABASES['default'] from env (SQLite lab / Postgres or MySQL prod)."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Any, Dict, Optional

import dj_database_url


def _sqlite_default(base_dir: Path) -> Dict[str, Any]:
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DB_NAME", str(base_dir / "db.sqlite3")),
    }


def _resolve_render_postgres_host(host: str, env: Dict[str, str]) -> str:
    """
    Upgrade a bare Render internal Postgres hostname (``dpg-...-a``) to its
    external FQDN (``dpg-...-a.<region>-postgres.render.com``) when internal
    DNS resolution fails (e.g. web service in Singapore and DB in Oregon).
    """
    if not host or not host.startswith("dpg-") or "." in host:
        return host
    try:
        socket.getaddrinfo(host, None)
        return host
    except socket.gaierror:
        region = (env.get("RENDER_DB_REGION") or "oregon").strip()
        return f"{host}.{region}-postgres.render.com"


def build_databases(
    base_dir: Path,
    environ: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Return DATABASES mapping.

    Priority:
      1. DATABASE_URL (parsed by dj-database-url, handles sslmode/query params)
      2. DB_ENGINE (+ DB_NAME/USER/PASSWORD/HOST/PORT)
      3. SQLite under base_dir/db.sqlite3
    """
    env = environ if environ is not None else os.environ
    conn_max_age = int(env.get("DB_CONN_MAX_AGE", "600") or "600")

    url = (env.get("DATABASE_URL") or "").strip()
    if url:
        # dj-database-url handles postgres://, mysql://, sqlite://, and query params
        is_sqlite = url.startswith("sqlite:")
        config = dj_database_url.parse(
            url,
            conn_max_age=0 if is_sqlite else conn_max_age,
            ssl_require=not is_sqlite,
        )
        if config.get("HOST"):
            config["HOST"] = _resolve_render_postgres_host(str(config["HOST"]), env)
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
                "PASSWORD": env.get("PASSWORD" if "PASSWORD" in env else "DB_PASSWORD", ""),
                "HOST": _resolve_render_postgres_host(env.get("DB_HOST", ""), env),
                "PORT": env.get("DB_PORT", ""),
            }

    if config["ENGINE"] != "django.db.backends.sqlite3":
        config.setdefault("CONN_MAX_AGE", conn_max_age)
        config.setdefault("OPTIONS", {})
        if config["ENGINE"] == "django.db.backends.mysql":
            # Avoid strict surprises with older dumps; PA MySQL is utf8mb4 by default.
            config["OPTIONS"].setdefault("charset", "utf8mb4")

    return {"default": config}
