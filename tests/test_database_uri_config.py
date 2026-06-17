import os
import importlib
import unittest

from app import _require_database_uri, _should_auto_create_tables
import app.config as app_config


class DatabaseUriConfigTests(unittest.TestCase):
    def setUp(self):
        self._old_database_url = os.environ.get("DATABASE_URL")
        self._old_flask_env = os.environ.get("FLASK_ENV")

    def tearDown(self):
        if self._old_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._old_database_url

        if self._old_flask_env is None:
            os.environ.pop("FLASK_ENV", None)
        else:
            os.environ["FLASK_ENV"] = self._old_flask_env

    def test_require_database_uri_uses_local_sqlite_fallback_when_unset(self):
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("FLASK_ENV", None)

        result = _require_database_uri()

        self.assertTrue(result.startswith("sqlite:///"))
        self.assertIn("instance/dev.db", result)

    def test_require_database_uri_converts_postgres_scheme(self):
        os.environ["DATABASE_URL"] = "postgres://user:pass@localhost:5432/appdb"
        result = _require_database_uri()
        self.assertEqual(result, "postgresql://user:pass@localhost:5432/appdb")

    def test_require_database_uri_adds_sslmode_for_supabase_pooler(self):
        os.environ["DATABASE_URL"] = (
            "postgresql://user:pass@aws-1-ap-south-1.pooler.supabase.com:5432/gramscs"
        )
        result = _require_database_uri()
        self.assertEqual(
            result,
            "postgresql://user:pass@aws-1-ap-south-1.pooler.supabase.com:5432/gramscs?sslmode=require",
        )

    def test_require_database_uri_keeps_existing_sslmode_for_supabase_pooler(self):
        os.environ["DATABASE_URL"] = (
            "postgresql://user:pass@aws-1-ap-south-1.pooler.supabase.com:5432/gramscs?sslmode=require"
        )
        result = _require_database_uri()
        self.assertEqual(
            result,
            "postgresql://user:pass@aws-1-ap-south-1.pooler.supabase.com:5432/gramscs?sslmode=require",
        )

    def test_should_auto_create_tables_is_disabled_in_production(self):
        old_auto_create_tables = os.environ.get("AUTO_CREATE_TABLES")
        try:
            os.environ["FLASK_ENV"] = "production"
            os.environ["AUTO_CREATE_TABLES"] = "true"

            self.assertFalse(_should_auto_create_tables())
        finally:
            if old_auto_create_tables is None:
                os.environ.pop("AUTO_CREATE_TABLES", None)
            else:
                os.environ["AUTO_CREATE_TABLES"] = old_auto_create_tables

    def test_resolve_secret_key_uses_local_fallback_outside_production(self):
        old_secret_key = os.environ.pop("SECRET_KEY", None)
        old_flask_env = os.environ.pop("FLASK_ENV", None)
        try:
            importlib.reload(app_config)
            self.assertEqual(app_config.SECRET_KEY, "dev-local-secret-key")
        finally:
            if old_secret_key is None:
                os.environ.pop("SECRET_KEY", None)
            else:
                os.environ["SECRET_KEY"] = old_secret_key

            if old_flask_env is None:
                os.environ.pop("FLASK_ENV", None)
            else:
                os.environ["FLASK_ENV"] = old_flask_env

            importlib.reload(app_config)


if __name__ == "__main__":
    unittest.main()