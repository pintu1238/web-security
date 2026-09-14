import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest import mock


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class FakeCursor:
    def __init__(self, connection=None, row=None, rows=None, description=None):
        self.connection = connection
        self.row = row
        self.rows = rows or []
        self.description = description or []

    def _apply_row_factory(self, row):
        if self.connection is None or self.connection.row_factory is None:
            return row
        return self.connection.row_factory(self, row)

    def fetchone(self):
        if self.row is None:
            return None
        return self._apply_row_factory(self.row)

    def fetchall(self):
        return [self._apply_row_factory(row) for row in self.rows]


class FakeConnection:
    def __init__(self):
        self.row_factory = None
        self.sql_statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.sql_statements.append(sql)
        if "sqlite_master" in sql:
            return FakeCursor(
                connection=self,
                row=(1,),
                description=(("exists",),),
            )
        return FakeCursor(
            connection=self,
            rows=[
                (
                    "chunk-1",
                    "sample text",
                    "sample law",
                    "sample section",
                    1,
                )
            ],
            description=(
                ("chunk_id",),
                ("chunk_text",),
                ("law_name",),
                ("section_name",),
                ("page_number",),
            ),
        )


class MissingPath:
    def exists(self):
        return False


class DatabaseConnectionTests(unittest.TestCase):
    def setUp(self):
        sys.modules.pop("database", None)
        os.environ.pop("TURSO_DATABASE_URL", None)
        os.environ.pop("TURSO_AUTH_TOKEN", None)

    def tearDown(self):
        sys.modules.pop("database", None)
        os.environ.pop("TURSO_DATABASE_URL", None)
        os.environ.pop("TURSO_AUTH_TOKEN", None)

    def import_database(self):
        with mock.patch("dotenv.load_dotenv"):
            return importlib.import_module("database")

    def test_connect_database_uses_local_sqlite_when_turso_env_is_missing(self):
        database = self.import_database()

        with mock.patch.object(database.sqlite3, "connect") as sqlite_connect:
            database.connect_database()

        sqlite_connect.assert_called_once_with(database.SQLITE_DB_PATH)

    def test_connect_database_uses_turso_when_credentials_are_present(self):
        os.environ["TURSO_DATABASE_URL"] = "libsql://example.turso.io"
        os.environ["TURSO_AUTH_TOKEN"] = "secret-token"
        import turso_serverless

        database = self.import_database()

        with mock.patch.object(turso_serverless, "connect") as turso_connect:
            database.connect_database()

        turso_connect.assert_called_once_with(
            "libsql://example.turso.io",
            auth_token="secret-token",
        )

    def test_get_all_chunks_reads_remote_database_when_local_file_is_missing(self):
        os.environ["TURSO_DATABASE_URL"] = "libsql://example.turso.io"
        os.environ["TURSO_AUTH_TOKEN"] = "secret-token"
        import turso_serverless

        fake_connection = FakeConnection()
        database = self.import_database()

        with (
            mock.patch.object(turso_serverless, "connect", return_value=fake_connection),
            mock.patch.object(database, "SQLITE_DB_PATH", MissingPath()),
        ):
            rows = database.get_all_chunks()

        self.assertEqual(rows[0]["chunk_id"], "chunk-1")
        self.assertEqual(len(fake_connection.sql_statements), 2)


if __name__ == "__main__":
    unittest.main()
