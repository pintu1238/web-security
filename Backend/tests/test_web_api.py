import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from scanning import FetchResponse


def make_pdf(text):
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.documents_dir = root / "legal_documents"
        self.documents_dir.mkdir()
        (self.documents_dir / "Electronic Transactions Act.pdf").write_bytes(
            make_pdf(
                "Electronic records and digital signatures receive legal recognition. "
                "Unauthorized access to computer systems may result in penalties."
            )
        )
        self.app = create_app(
            {
                "TESTING": True,
                "WORKSPACE_DB": str(root / "workspace.db"),
                "LEGAL_DOCUMENTS_DIR": str(self.documents_dir),
            }
        )
        self.client = self.app.test_client()
        # Model inference is the external boundary; keep PDF retrieval and storage real.
        model = patch('requests.post', side_effect=__import__('requests').ConnectionError('offline test'))
        model.start()
        self.addCleanup(model.stop)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_health_dashboard_and_seeded_tasks_use_persisted_defaults(self):
        self.assertEqual(self.client.get("/api/health").get_json(), {"status": "ok"})

        tasks = self.client.get("/api/tasks").get_json()
        self.assertEqual(len(tasks), 6)
        self.assertTrue(all(item["status"] == "pending" for item in tasks))
        self.assertTrue(all(item["due_date"] is None for item in tasks))
        self.assertEqual(
            {item["title"] for item in tasks},
            {
                "Publish a privacy notice",
                "Review access controls",
                "Verify business backups",
                "Organize employment records",
                "Organize business registration records",
                "Create an incident response plan",
            },
        )

        dashboard = self.client.get("/api/dashboard").get_json()
        self.assertEqual(dashboard["profile"]["business_name"], "My business")
        self.assertEqual(dashboard["stats"]["compliance_total"], 6)
        self.assertEqual(dashboard["stats"]["compliance_completed"], 0)
        self.assertIsNone(dashboard["stats"]["security_score"])
        self.assertEqual(dashboard["stats"]["open_findings"], 0)
        self.assertEqual(dashboard["stats"]["documents_count"], 0)

    def test_frontend_assets_are_served_from_the_web_directory(self):
        index = self.client.get("/")
        stylesheet = self.client.get("/assets/styles.css")
        script = self.client.get("/assets/app.js")
        self.addCleanup(index.close)
        self.addCleanup(stylesheet.close)
        self.addCleanup(script.close)
        self.assertEqual(index.status_code, 200)
        self.assertEqual(stylesheet.status_code, 200)
        self.assertEqual(script.status_code, 200)
        self.assertIn("text/css", stylesheet.content_type)
        self.assertIn("javascript", script.content_type)

    def test_settings_update_persists_and_rejects_invalid_or_unknown_values(self):
        response = self.client.put(
            "/api/settings",
            json={
                "business_name": "Everest Systems",
                "owner": "Asha Rai",
                "email": "asha@example.com",
                "website": "https://example.com",
                "business_type": "IT / Software",
                "address": "Kathmandu",
                "notifications": False,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["business_name"], "Everest Systems")
        self.assertFalse(self.client.get("/api/settings").get_json()["notifications"])

        invalid = self.client.put("/api/settings", json={"email": "not-an-email"})
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("error", invalid.get_json())
        unknown = self.client.put("/api/settings", json={"role": "admin"})
        self.assertEqual(unknown.status_code, 400)

    def test_settings_accept_the_frontend_declared_field_limits(self):
        local = "a" * 64
        domain = "b" * 63 + "." + "c" * 63 + "." + "d" * 61
        email = local + "@" + domain
        self.assertEqual(len(email), 254)
        website = "https://example.com/" + "w" * (2048 - len("https://example.com/"))
        response = self.client.put(
            "/api/settings",
            json={
                "business_name": "B" * 150,
                "owner": "O" * 150,
                "email": email,
                "website": website,
                "address": "A" * 1000,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_settings_reject_malformed_websites_as_client_errors(self):
        for website in (
            "https://[broken",
            "https://example.com:not-a-port",
            "https://user:secret@example.com",
            "https://exa mple.com",
        ):
            with self.subTest(website=website):
                response = self.client.put("/api/settings", json={"website": website})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(set(response.get_json()), {"error"})

    def test_task_lifecycle_validates_fields_and_updates_dashboard_stats(self):
        bad = self.client.post(
            "/api/tasks",
            json={"title": "Audit", "category": "Other", "priority": "urgent", "due_date": "soon"},
        )
        self.assertEqual(bad.status_code, 400)

        created_response = self.client.post(
            "/api/tasks",
            json={
                "title": "Review supplier access",
                "category": "Security",
                "priority": "high",
                "due_date": "2026-10-01",
            },
        )
        self.assertEqual(created_response.status_code, 201)
        created = created_response.get_json()
        self.assertEqual(created["description"], "")
        self.assertEqual(created["status"], "pending")

        completed = self.client.patch(
            f"/api/tasks/{created['id']}", json={"status": "completed"}
        )
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.get_json()["status"], "completed")
        self.assertEqual(
            self.client.get("/api/dashboard").get_json()["stats"]["compliance_completed"],
            1,
        )

        deleted = self.client.delete(f"/api/tasks/{created['id']}")
        self.assertEqual(deleted.get_json(), {"ok": True})
        self.assertEqual(self.client.delete(f"/api/tasks/{created['id']}").status_code, 404)

    def test_deleted_starter_tasks_do_not_reappear_when_workspace_reopens(self):
        for task in self.client.get("/api/tasks").get_json():
            self.assertEqual(self.client.delete(f"/api/tasks/{task['id']}").status_code, 200)
        self.assertEqual(self.client.get("/api/tasks").get_json(), [])

        reopened = create_app(
            {
                "TESTING": True,
                "WORKSPACE_DB": self.app.config["WORKSPACE_DB"],
                "LEGAL_DOCUMENTS_DIR": str(self.documents_dir),
            }
        )
        with reopened.test_client() as client:
            self.assertEqual(client.get("/api/tasks").get_json(), [])

    def test_knowledge_lists_real_pdf_searches_text_and_saves_conversations(self):
        knowledge = self.client.get("/api/knowledge").get_json()
        self.assertEqual(len(knowledge), 1)
        self.assertEqual(knowledge[0]["pages"], 1)
        self.assertGreater(knowledge[0]["size"], 0)

        download = self.client.get(knowledge[0]["url"])
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.mimetype, "application/pdf")
        download.close()

        response = self.client.post(
            "/api/search", json={"question": "Are digital signatures recognized?"}
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["source"], "local_documents")
        self.assertTrue(payload["results"])
        self.assertEqual(payload["results"][0]["retrieval_method"], "bm25")
        self.assertEqual(payload["results"][0]["metadata"]["page_number"], 1)
        self.assertIn("digital signatures", payload["results"][0]["text"].lower())

        conversations = self.client.get("/api/conversations").get_json()
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0]["question"], "Are digital signatures recognized?")
        self.assertEqual(self.client.delete("/api/conversations").get_json(), {"ok": True})
        self.assertEqual(self.client.get("/api/conversations").get_json(), [])

    def test_search_handles_greeting_no_results_and_malformed_requests(self):
        greeting = self.client.post("/api/search", json={"question": "Namaste!"})
        self.assertEqual(greeting.status_code, 200)
        self.assertEqual(greeting.get_json()["results"], [])
        self.assertEqual(greeting.get_json()["source"], "conversation")

        missing = self.client.post("/api/search", json={})
        self.assertEqual(missing.status_code, 400)
        malformed = self.client.post(
            "/api/search", data="{", content_type="application/json"
        )
        self.assertEqual(malformed.status_code, 400)
        no_match = self.client.post(
            "/api/search", json={"question": "According to the PDFs, what is the maritime lobster quota?"}
        ).get_json()
        self.assertEqual(no_match["results"], [])
        self.assertIn("could not find", no_match["answer"].lower())

    def test_conversations_are_returned_in_chronological_order(self):
        first = "Are digital signatures recognized?"
        second = "What does the Act say about unauthorized access?"
        self.assertEqual(self.client.post("/api/search", json={"question": first}).status_code, 200)
        self.assertEqual(self.client.post("/api/search", json={"question": second}).status_code, 200)
        conversations = self.client.get("/api/conversations").get_json()
        self.assertEqual([item["question"] for item in conversations], [first, second])

    def test_selected_conversation_can_be_deleted_without_deleting_other_history(self):
        self.assertEqual(self.client.post("/api/search", json={"question": "First saved question"}).status_code, 200)
        self.assertEqual(self.client.post("/api/search", json={"question": "Second saved question"}).status_code, 200)
        conversations = self.client.get("/api/conversations").get_json()
        selected_id = conversations[1]["id"]

        deleted = self.client.delete(f"/api/conversations/{selected_id}")

        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.get_json(), {"ok": True})
        remaining = self.client.get("/api/conversations").get_json()
        self.assertEqual([item["question"] for item in remaining], ["First saved question"])
        self.assertEqual(self.client.delete(f"/api/conversations/{selected_id}").status_code, 404)

    def test_pdf_upload_uses_safe_name_and_rejects_duplicates_and_image_only_pdf(self):
        new_pdf = make_pdf("A privacy notice explains collection and use of personal data.")
        response = self.client.post(
            "/api/knowledge",
            data={"file": (io.BytesIO(new_pdf), "../../Privacy Notes.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201)
        created = response.get_json()
        self.assertNotIn("..", created["file_name"])
        self.assertTrue((self.documents_dir / created["file_name"]).is_file())

        duplicate = self.client.post(
            "/api/knowledge",
            data={"file": (io.BytesIO(new_pdf), "copy.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(duplicate.status_code, 409)

        blank = pymupdf.open()
        blank.new_page()
        blank_bytes = blank.tobytes()
        blank.close()
        image_only = self.client.post(
            "/api/knowledge",
            data={"file": (io.BytesIO(blank_bytes), "blank.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(image_only.status_code, 400)
        self.assertIn("text", image_only.get_json()["error"].lower())

    def test_document_generation_download_and_export_use_persisted_data(self):
        invalid = self.client.post(
            "/api/documents",
            json={
                "type": "will",
                "business_name": "Everest Systems",
                "owner": "Asha Rai",
                "address": "Kathmandu",
                "effective_date": "today",
            },
        )
        self.assertEqual(invalid.status_code, 400)

        created_response = self.client.post(
            "/api/documents",
            json={
                "type": "privacy_policy",
                "business_name": "Everest Systems",
                "owner": "Asha Rai",
                "address": "Kathmandu",
                "effective_date": "2026-09-14",
            },
        )
        self.assertEqual(created_response.status_code, 201)
        created = created_response.get_json()
        self.assertIn("Everest Systems", created["content"])
        self.assertIn("draft", created["content"].lower())
        self.assertIn("review", created["content"].lower())

        download = self.client.get(f"/api/documents/{created['id']}/download")
        self.assertEqual(download.status_code, 200)
        self.assertIn("attachment", download.headers["Content-Disposition"])
        self.assertIn("Everest Systems", download.get_data(as_text=True))

        exported = self.client.get("/api/export")
        self.assertEqual(exported.status_code, 200)
        self.assertIn("attachment", exported.headers["Content-Disposition"])
        export_payload = json.loads(exported.get_data(as_text=True))
        self.assertEqual(len(export_payload["documents"]), 1)
        self.assertTrue(export_payload["activity"])

    def test_saved_document_can_be_deleted_and_stays_deleted_after_restart(self):
        created = self.client.post(
            "/api/documents",
            json={
                "type": "privacy_policy",
                "business_name": "Everest Systems",
                "owner": "Asha Rai",
                "address": "Kathmandu",
                "effective_date": "2026-09-14",
            },
        ).get_json()

        deleted = self.client.delete(f"/api/documents/{created['id']}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.get_json(), {"ok": True})
        self.assertEqual(self.client.get(f"/api/documents/{created['id']}").status_code, 404)
        self.assertEqual(self.client.get("/api/documents").get_json(), [])
        self.assertEqual(self.client.delete(f"/api/documents/{created['id']}").status_code, 404)

        reopened = create_app({
            "TESTING": True,
            "WORKSPACE_DB": self.app.config["WORKSPACE_DB"],
            "LEGAL_DOCUMENTS_DIR": self.app.config["LEGAL_DOCUMENTS_DIR"],
        }).test_client()
        self.assertEqual(reopened.get("/api/documents").get_json(), [])
        self.assertTrue(any(item["title"] == "Draft document deleted"
                            for item in reopened.get("/api/dashboard").get_json()["activity"]))

    def test_document_fields_accept_saved_profile_limits(self):
        response = self.client.post(
            "/api/documents",
            json={
                "type": "nda",
                "business_name": "B" * 150,
                "owner": "O" * 150,
                "address": "A" * 600,
                "effective_date": "2026-09-14",
            },
        )
        self.assertEqual(response.status_code, 201)
        too_long = self.client.post(
            "/api/documents",
            json={
                "type": "nda",
                "business_name": "B" * 151,
                "owner": "Owner",
                "address": "Kathmandu",
                "effective_date": "2026-09-14",
            },
        )
        self.assertEqual(too_long.status_code, 400)

    def test_scan_requires_consent_and_rejects_private_destinations(self):
        missing_consent = self.client.post(
            "/api/scans", json={"url": "https://93.184.216.34"}
        )
        self.assertEqual(missing_consent.status_code, 400)

        for url in (
            "http://127.0.0.1",
            "http://[::1]",
            "http://169.254.169.254/latest/meta-data",
            "http://user:pass@example.com",
            "http://service.internal",
        ):
            with self.subTest(url=url):
                response = self.client.post("/api/scans", json={"url": url, "authorized": True})
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())

    def test_scan_classifies_passive_headers_persists_report_and_validates_redirect(self):
        secure_headers = {
            "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
            "strict-transport-security": "max-age=31536000",
            "x-content-type-options": "nosniff",
            "referrer-policy": "strict-origin-when-cross-origin",
        }
        with patch(
            "scanning._fetch_once",
            return_value=FetchResponse(status=200, headers=secure_headers, body=b"ok"),
        ):
            response = self.client.post(
                "/api/scans", json={"url": "https://93.184.216.34", "authorized": True}
            )
        self.assertEqual(response.status_code, 201)
        scan = response.get_json()
        self.assertEqual(scan["score"], 100)
        self.assertEqual(scan["checks_passed"], 6)
        self.assertEqual(scan["checks_total"], 6)
        self.assertEqual(scan["findings"], [])
        self.assertEqual(self.client.get("/api/scans").get_json()[0]["id"], scan["id"])
        report = self.client.get(f"/api/scans/{scan['id']}/report")
        self.assertEqual(report.status_code, 200)
        self.assertIn("passive website security assessment", report.get_data(as_text=True).lower())

        with patch(
            "scanning._fetch_once",
            return_value=FetchResponse(
                status=302,
                headers={"location": "http://127.0.0.1/admin"},
                body=b"",
            ),
        ):
            redirect = self.client.post(
                "/api/scans", json={"url": "http://93.184.216.34", "authorized": True}
            )
        self.assertEqual(redirect.status_code, 400)

    def test_api_errors_are_json(self):
        response = self.client.get("/api/scans/999/report")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(set(response.get_json()), {"error"})


if __name__ == "__main__":
    unittest.main()
