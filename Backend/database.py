import os
import sqlite3
from pathlib import Path

from config import SQLITE_DB_PATH

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv(Path(__file__).resolve().parent / ".env")


def has_turso_credentials():
    """Return True when the backend has enough information to use Turso."""

    return bool(os.getenv("TURSO_DATABASE_URL") and os.getenv("TURSO_AUTH_TOKEN"))


def connect_database():
    """Connect to Turso when configured, otherwise use the local SQLite file."""

    if has_turso_credentials():
        import turso_serverless

        return turso_serverless.connect(
            os.environ["TURSO_DATABASE_URL"],
            auth_token=os.environ["TURSO_AUTH_TOKEN"],
        )

    return sqlite3.connect(SQLITE_DB_PATH)


def database_row_factory():
    """Choose a row factory compatible with the active database driver."""

    if has_turso_credentials():
        from turso_serverless.connection import Row

        return Row

    return sqlite3.Row


def initialize_database():
    """Create the legal document tables when they do not exist."""

    with connect_database() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS legal_documents (
                document_id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                law_name TEXT NOT NULL,
                source TEXT,
                document_version TEXT
            );

            CREATE TABLE IF NOT EXISTS legal_chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id INTEGER NOT NULL,
                law_name TEXT NOT NULL,
                section_name TEXT,
                page_number INTEGER,
                chunk_text TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES legal_documents(document_id)
            );
            """
        )


def add_document(file_name, law_name, source, document_version):
    """Insert a legal document and return its database identifier."""

    with connect_database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO legal_documents
                (file_name, law_name, source, document_version)
            VALUES (?, ?, ?, ?)
            """,
            (file_name, law_name, source, document_version),
        )
        document_id = cursor.lastrowid
        cursor.close()

    return document_id


def add_chunk(
    document_id,
    chunk_id,
    law_name,
    section_name,
    page_number,
    chunk_text,
):
    """Insert or update one searchable legal text chunk."""

    with connect_database() as connection:
        connection.execute(
            """
            INSERT INTO legal_chunks
                (chunk_id, document_id, law_name, section_name, page_number, chunk_text)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
                document_id = excluded.document_id,
                law_name = excluded.law_name,
                section_name = excluded.section_name,
                page_number = excluded.page_number,
                chunk_text = excluded.chunk_text
            """,
            (
                chunk_id,
                document_id,
                law_name,
                section_name,
                page_number,
                chunk_text,
            ),
        )


def get_all_chunks():
    """Return all indexed legal chunks as dictionary-like rows."""

    if not has_turso_credentials() and not SQLITE_DB_PATH.exists():
        return []

    with connect_database() as connection:
        connection.row_factory = database_row_factory()

        table_exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = 'legal_chunks'
            """
        ).fetchone()

        if table_exists is None:
            return []

        rows = connection.execute(
            """
            SELECT chunk_id, chunk_text, law_name, section_name, page_number
            FROM legal_chunks
            ORDER BY chunk_id
            """
        ).fetchall()

    return rows
