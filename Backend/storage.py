import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


STARTER_TASKS = (
    ("Publish a privacy notice", "Explain what personal data the business collects, uses, retains, and shares.", "Legal", "high"),
    ("Review access controls", "Confirm each person has only the system access needed for their role.", "Security", "high"),
    ("Verify business backups", "Check that important data is backed up and that a restore can be completed.", "Operations", "high"),
    ("Organize employment records", "Keep employment agreements and related staff records current and accessible.", "Legal", "medium"),
    ("Organize business registration records", "Keep registration, renewal, and ownership records together.", "Operations", "low"),
    ("Create an incident response plan", "Write down who will contain, assess, communicate, and recover from an incident.", "Security", "medium"),
)

DEFAULT_PROFILE = {
    "business_name": "My business",
    "owner": "",
    "email": "",
    "website": "",
    "business_type": "IT / Software",
    "address": "",
    "notifications": True,
}


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@contextmanager
def connect(db_path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize(db_path):
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                business_name TEXT NOT NULL,
                owner TEXT NOT NULL,
                email TEXT NOT NULL,
                website TEXT NOT NULL,
                business_type TEXT NOT NULL,
                address TEXT NOT NULL,
                notifications INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                due_date TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                score INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                checks_passed INTEGER NOT NULL,
                checks_total INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT NOT NULL,
                recommendation TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS generated_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                business_name TEXT NOT NULL,
                owner TEXT NOT NULL,
                address TEXT NOT NULL,
                effective_date TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL,
                type TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                results_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS workspace_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                chat_revision INTEGER NOT NULL DEFAULT 0
            );
            INSERT OR IGNORE INTO workspace_state (id, chat_revision) VALUES (1, 0);
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                file_name TEXT NOT NULL,
                pages INTEGER NOT NULL,
                size INTEGER NOT NULL
            );
            """
        )
        profile_insert = connection.execute(
            """INSERT OR IGNORE INTO settings
               (id, business_name, owner, email, website, business_type, address, notifications)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?)""",
            (
                DEFAULT_PROFILE["business_name"],
                DEFAULT_PROFILE["owner"],
                DEFAULT_PROFILE["email"],
                DEFAULT_PROFILE["website"],
                DEFAULT_PROFILE["business_type"],
                DEFAULT_PROFILE["address"],
                int(DEFAULT_PROFILE["notifications"]),
            ),
        )
        if profile_insert.rowcount == 1:
            connection.executemany(
                """INSERT INTO tasks
                   (title, description, category, priority, status, due_date, created_at)
                   VALUES (?, ?, ?, ?, 'pending', NULL, ?)""",
                [(*task, now_iso()) for task in STARTER_TASKS],
            )


def _profile(row):
    result = dict(row)
    result.pop("id", None)
    result["notifications"] = bool(result["notifications"])
    return result


def get_profile(db_path):
    with connect(db_path) as connection:
        return _profile(connection.execute("SELECT * FROM settings WHERE id = 1").fetchone())


def update_profile(db_path, updates):
    if updates:
        columns = ", ".join(f"{key} = ?" for key in updates)
        values = [int(value) if key == "notifications" else value for key, value in updates.items()]
        with connect(db_path) as connection:
            connection.execute(f"UPDATE settings SET {columns} WHERE id = 1", values)
            add_activity(connection, "Business profile updated", "Saved workspace settings.", "settings")
    return get_profile(db_path)


def task_dict(row):
    return {key: row[key] for key in ("id", "title", "description", "category", "priority", "status", "due_date")}


def list_tasks(db_path):
    with connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM tasks ORDER BY id").fetchall()
        return [task_dict(row) for row in rows]


def get_task(db_path, task_id):
    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return task_dict(row) if row else None


def create_task(db_path, values):
    with connect(db_path) as connection:
        cursor = connection.execute(
            """INSERT INTO tasks
               (title, description, category, priority, status, due_date, created_at)
               VALUES (?, '', ?, ?, 'pending', ?, ?)""",
            (values["title"], values["category"], values["priority"], values["due_date"], now_iso()),
        )
        task_id = cursor.lastrowid
        add_activity(connection, "Task added", values["title"], "task")
    return get_task(db_path, task_id)


def update_task_status(db_path, task_id, status):
    with connect(db_path) as connection:
        row = connection.execute("SELECT title FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return None
        connection.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        detail = f"{row['title']} marked {status}."
        add_activity(connection, "Task updated", detail, "task")
    return get_task(db_path, task_id)


def delete_task(db_path, task_id):
    with connect(db_path) as connection:
        row = connection.execute("SELECT title FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return False
        connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        add_activity(connection, "Task removed", row["title"], "task")
        return True


def add_activity(connection, title, detail, activity_type):
    connection.execute(
        "INSERT INTO activity (title, detail, created_at, type) VALUES (?, ?, ?, ?)",
        (title, detail, now_iso(), activity_type),
    )


def list_activity(db_path):
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, title, detail, created_at, type FROM activity ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def save_scan(db_path, url, assessment):
    with connect(db_path) as connection:
        created_at = now_iso()
        cursor = connection.execute(
            """INSERT INTO scans (url, score, created_at, checks_passed, checks_total)
               VALUES (?, ?, ?, ?, ?)""",
            (url, assessment["score"], created_at, assessment["checks_passed"], assessment["checks_total"]),
        )
        scan_id = cursor.lastrowid
        for finding in assessment["findings"]:
            connection.execute(
                """INSERT INTO findings
                   (scan_id, title, severity, status, description, recommendation)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    scan_id,
                    finding["title"],
                    finding["severity"],
                    finding["status"],
                    finding["description"],
                    finding["recommendation"],
                ),
            )
        add_activity(
            connection,
            "Website assessment completed",
            f"Passive checks for {url} scored {assessment['score']}/100.",
            "scan",
        )
    return get_scan(db_path, scan_id)


def _findings(connection, scan_id):
    rows = connection.execute(
        """SELECT id, title, severity, status, description, recommendation
           FROM findings WHERE scan_id = ? ORDER BY id""",
        (scan_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def scan_dict(connection, row):
    result = dict(row)
    result["findings"] = _findings(connection, row["id"])
    return result


def get_scan(db_path, scan_id):
    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
        return scan_dict(connection, row) if row else None


def list_scans(db_path):
    with connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM scans ORDER BY id DESC").fetchall()
        return [scan_dict(connection, row) for row in rows]


def save_document(db_path, values, title, content):
    with connect(db_path) as connection:
        created_at = now_iso()
        cursor = connection.execute(
            """INSERT INTO generated_documents
               (type, title, business_name, owner, address, effective_date, content, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                values["type"], title, values["business_name"], values["owner"],
                values["address"], values["effective_date"], content, created_at,
            ),
        )
        document_id = cursor.lastrowid
        add_activity(connection, "Draft document created", title, "document")
    return get_document(db_path, document_id, include_content=True)


def document_dict(row, include_content=False):
    keys = ["id", "type", "title", "business_name", "created_at"]
    if include_content:
        keys += ["owner", "address", "effective_date", "content"]
    return {key: row[key] for key in keys}


def get_document(db_path, document_id, include_content=False):
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM generated_documents WHERE id = ?", (document_id,)
        ).fetchone()
        return document_dict(row, include_content) if row else None


def list_documents(db_path, include_content=False):
    with connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM generated_documents ORDER BY id DESC").fetchall()
        return [document_dict(row, include_content) for row in rows]


def chat_revision(db_path):
    with connect(db_path) as connection:
        return connection.execute("SELECT chat_revision FROM workspace_state WHERE id = 1").fetchone()[0]


def save_conversation(db_path, question, answer, results, expected_revision=None):
    with connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        revision = connection.execute("SELECT chat_revision FROM workspace_state WHERE id = 1").fetchone()[0]
        if expected_revision is not None and revision != expected_revision:
            return None
        cursor = connection.execute(
            """INSERT INTO conversations (question, answer, results_json, created_at)
               VALUES (?, ?, ?, ?)""",
            (question, answer, json.dumps(results, ensure_ascii=False), now_iso()),
        )
        add_activity(connection, "Assistant answer saved", "A conversation was saved to your workspace.", "search")
        return cursor.lastrowid


def list_conversations(db_path):
    with connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM conversations ORDER BY id ASC").fetchall()
        return [
            {
                "id": row["id"],
                "question": row["question"],
                "answer": row["answer"],
                "results": json.loads(row["results_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


def clear_conversations(db_path):
    with connect(db_path) as connection:
        connection.execute("UPDATE workspace_state SET chat_revision = chat_revision + 1 WHERE id = 1")
        connection.execute("DELETE FROM conversations")


def sync_knowledge(db_path, records, uploaded=None):
    """Persist the catalog of real PDFs, including files present before an upgrade."""
    with connect(db_path) as connection:
        connection.executemany(
            """INSERT INTO knowledge_documents (id, title, file_name, pages, size)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET title=excluded.title, file_name=excluded.file_name,
                   pages=excluded.pages, size=excluded.size
               WHERE title != excluded.title OR file_name != excluded.file_name
                   OR pages != excluded.pages OR size != excluded.size""",
            [(r["id"], r["title"], r["file_name"], r["pages"], r["size"]) for r in records],
        )
        current_ids = {r["id"] for r in records}
        stale = [(r["id"],) for r in connection.execute("SELECT id FROM knowledge_documents") if r["id"] not in current_ids]
        connection.executemany("DELETE FROM knowledge_documents WHERE id = ?", stale)
        if uploaded:
            add_activity(connection, "PDF added to knowledge base", uploaded["title"], "upload")
        rows = connection.execute("SELECT * FROM knowledge_documents ORDER BY title COLLATE NOCASE, id").fetchall()
        return [{**dict(row), "url": f"/api/knowledge/{row['id']}/download"} for row in rows]


def stats(db_path):
    with connect(db_path) as connection:
        completed, total = connection.execute(
            "SELECT SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), COUNT(*) FROM tasks"
        ).fetchone()
        latest_scan = connection.execute("SELECT id, score FROM scans ORDER BY id DESC LIMIT 1").fetchone()
        open_findings = 0
        security_score = None
        if latest_scan:
            security_score = latest_scan["score"]
            open_findings = connection.execute(
                "SELECT COUNT(*) FROM findings WHERE scan_id = ? AND status = 'open'",
                (latest_scan["id"],),
            ).fetchone()[0]
        documents_count = connection.execute("SELECT COUNT(*) FROM generated_documents").fetchone()[0]
    return {
        "compliance_completed": completed or 0,
        "compliance_total": total,
        "security_score": security_score,
        "open_findings": open_findings,
        "documents_count": documents_count,
    }
