"""Regression checks for complete, database-backed workspace flows."""
import io
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app


class WorkspaceIntegrityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = {"TESTING": True, "WORKSPACE_DB": self.root / "workspace.db",
                       "LEGAL_DOCUMENTS_DIR": self.root / "pdfs"}
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def upload(self):
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text((72, 72), "Vendor access must be reviewed each month.")
            data = pdf.tobytes()
        response = self.client.post("/api/knowledge", data={"file": (io.BytesIO(data), "Vendor policy.pdf")})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def draft(self):
        response = self.client.post("/api/documents", json={"type": "nda",
            "business_name": "Audit Business", "owner": "Test Owner", "address": "Test Address",
            "effective_date": "2026-09-14"})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def test_export_contains_saved_draft_content_and_conversation_history(self):
        draft = self.draft()
        self.client.post("/api/search", json={"question": "hello"})
        reopened = create_app(self.config).test_client()
        exported = reopened.get("/api/export").get_json()
        self.assertEqual(exported["documents"][0].get("content"), draft["content"])
        self.assertEqual(exported.get("conversations", [{}])[0].get("question"), "hello")
        self.assertEqual(exported["documents"][0]["owner"], "Test Owner")

    def test_uploaded_pdf_is_catalogued_in_sqlite_and_visible_in_activity_and_export(self):
        uploaded = self.upload()
        reopened = create_app(self.config).test_client()
        dashboard = reopened.get("/api/dashboard").get_json()
        self.assertEqual([d["id"] for d in dashboard.get("knowledge", [])], [uploaded["id"]])
        self.assertTrue(any(a["type"] == "upload" and "Vendor" in a["detail"] for a in dashboard["activity"]))
        with closing(sqlite3.connect(self.config["WORKSPACE_DB"])) as connection:
            stored = connection.execute("SELECT id, title FROM knowledge_documents").fetchall()
        self.assertEqual(stored, [(uploaded["id"], uploaded["title"])])
        exported = reopened.get("/api/export").get_json()
        self.assertEqual(exported["knowledge"][0]["id"], uploaded["id"])
        self.assertNotIn("_path", exported["knowledge"][0])

    def test_saved_draft_can_be_reopened_after_app_restart(self):
        draft = self.draft()
        response = create_app(self.config).test_client().get(f"/api/documents/{draft['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["content"], draft["content"])
        self.assertEqual(self.client.get("/api/documents/999999").status_code, 404)

    def test_clearing_history_while_an_answer_is_pending_does_not_restore_it(self):
        def finish_after_clear(*args, **kwargs):
            self.assertEqual(self.app.test_client().delete("/api/conversations").status_code, 200)
            return {"answer": "A pending reply", "results": [], "mode": "conversation"}
        with patch("assistant.answer", side_effect=finish_after_clear):
            response = self.client.post("/api/search", json={"question": "hello"})
        self.assertEqual(self.client.get("/api/conversations").get_json(), [])
        self.assertEqual(response.status_code, 409)

    def test_workspace_api_does_not_allow_browser_cache_to_hide_database_changes(self):
        for path in ("/api/dashboard", "/api/settings", "/api/knowledge", "/api/conversations", "/api/export"):
            with self.subTest(path=path):
                self.assertIn("no-store", self.client.get(path).headers.get("Cache-Control", ""))


if __name__ == "__main__":
    unittest.main()
