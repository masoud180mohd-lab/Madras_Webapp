from pathlib import Path

from django.test import SimpleTestCase

from madrasa_sys.settings.db import build_databases, parse_database_url


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
        self.assertEqual(cfg["PORT"], "5433")

    def test_parse_rejects_mysql(self):
        with self.assertRaises(ValueError):
            parse_database_url("mysql://u:p@localhost/db")
