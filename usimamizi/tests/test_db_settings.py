from pathlib import Path

from django.test import SimpleTestCase

from madrasa_sys.settings.base import env_bool
from madrasa_sys.settings.db import build_databases


class DatabaseSettingsBuilderTests(SimpleTestCase):
    def setUp(self):
        self.base = Path("/tmp/madrasa-test-base")

    def test_default_sqlite(self):
        db = build_databases(self.base, environ={})
        self.assertEqual(db["default"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertTrue(str(db["default"]["NAME"]).endswith("db.sqlite3"))

    def test_discrete_postgres(self):
        db = build_databases(
            self.base,
            environ={
                "DB_ENGINE": "django.db.backends.postgresql",
                "DB_NAME": "madrasa",
                "DB_USER": "madrasa",
                "DB_PASSWORD": "secret",
                "DB_HOST": "127.0.0.1",
                "DB_PORT": "5432",
                "DB_CONN_MAX_AGE": "120",
            },
        )
        cfg = db["default"]
        self.assertEqual(cfg["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(cfg["NAME"], "madrasa")
        self.assertEqual(cfg["USER"], "madrasa")
        self.assertEqual(cfg["PASSWORD"], "secret")
        self.assertEqual(cfg["HOST"], "127.0.0.1")
        self.assertEqual(cfg["PORT"], "5432")
        self.assertEqual(cfg["CONN_MAX_AGE"], 120)

    def test_database_url_overrides(self):
        db = build_databases(
            self.base,
            environ={
                "DATABASE_URL": "postgres://u:p%40ss@db.example:5433/mydb",
                "DB_ENGINE": "django.db.backends.sqlite3",
            },
        )
        cfg = db["default"]
        self.assertEqual(cfg["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(cfg["NAME"], "mydb")
        self.assertEqual(cfg["USER"], "u")
        self.assertEqual(cfg["PASSWORD"], "p@ss")
        self.assertEqual(cfg["HOST"], "db.example")
        # dj-database-url returns PORT as an int for postgres URLs.
        self.assertEqual(int(cfg["PORT"]), 5433)
        # ssl_require=True injects sslmode into OPTIONS.
        self.assertEqual(cfg["OPTIONS"].get("sslmode"), "require")

    def test_discrete_mysql(self):
        db = build_databases(
            self.base,
            environ={
                "DB_ENGINE": "django.db.backends.mysql",
                "DB_NAME": "user$madrasa",
                "DB_USER": "user",
                "DB_PASSWORD": "x",
                "DB_HOST": "user.mysql.pythonanywhere-services.com",
                "DB_PORT": "3306",
            },
        )
        self.assertEqual(db["default"]["ENGINE"], "django.db.backends.mysql")
        self.assertEqual(db["default"]["OPTIONS"].get("charset"), "utf8mb4")

    def test_mysql_url_parsed(self):
        db = build_databases(
            self.base,
            environ={
                "DATABASE_URL": (
                    "mysql://pa_user:secret@"
                    "pa_user.mysql.pythonanywhere-services.com:3306/pa_user$madrasa"
                ),
            },
        )
        cfg = db["default"]
        self.assertEqual(cfg["ENGINE"], "django.db.backends.mysql")
        self.assertEqual(cfg["NAME"], "pa_user$madrasa")
        self.assertEqual(cfg["HOST"], "pa_user.mysql.pythonanywhere-services.com")
        self.assertEqual(int(cfg["PORT"]), 3306)

    def test_ssl_require_adds_options(self):
        db = build_databases(
            self.base,
            environ={"DATABASE_URL": "postgres://u:p@db.example:5432/mydb"},
        )
        cfg = db["default"]
        self.assertEqual(cfg["OPTIONS"].get("sslmode"), "require")

    def test_unknown_scheme_raises(self):
        # oracle:// is now a supported scheme, so use a genuinely unknown one.
        with self.assertRaises(ValueError):
            build_databases(
                self.base,
                environ={"DATABASE_URL": "nosuchdb://u:p@localhost/db"},
            )

    def test_conn_max_age_passthrough(self):
        db = build_databases(
            self.base,
            environ={
                "DATABASE_URL": "postgres://u:p@db.example:5432/mydb",
                "DB_CONN_MAX_AGE": "120",
            },
        )
        self.assertEqual(db["default"]["CONN_MAX_AGE"], 120)

    def test_allow_sqlite_env_flag(self):
        import os

        os.environ.pop("DJANGO_ALLOW_SQLITE", None)
        self.assertFalse(env_bool("DJANGO_ALLOW_SQLITE", False))
        os.environ["DJANGO_ALLOW_SQLITE"] = "True"
        try:
            self.assertTrue(env_bool("DJANGO_ALLOW_SQLITE", False))
        finally:
            os.environ.pop("DJANGO_ALLOW_SQLITE", None)

    def test_render_internal_host_fallback(self):
        db = build_databases(
            self.base,
            environ={
                "DATABASE_URL": "postgresql://u:p@dpg-db9u6vu1egvs738l39v0-a/madrasa_db",
                "RENDER_DB_REGION": "oregon",
            },
        )
        self.assertEqual(
            db["default"]["HOST"],
            "dpg-db9u6vu1egvs738l39v0-a.oregon-postgres.render.com",
        )
