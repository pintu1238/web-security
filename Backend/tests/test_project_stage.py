import tempfile
import unittest
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app


class ProjectStageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.app = create_app(
            {
                "TESTING": True,
                "WORKSPACE_DB": str(root / "workspace.db"),
                "LEGAL_DOCUMENTS_DIR": str(root / "legal_documents"),
                "PROJECT_STAGE": "part_a",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_part_a_keeps_all_frontend_pages_but_marks_part_b_features(self):
        response = self.client.get("/api/project-config")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["stage"], "part_a")
        self.assertEqual(
            payload["pages"],
            [
                "dashboard",
                "scanner",
                "compliance",
                "assistant",
                "documents",
                "knowledge",
                "admin",
                "user",
                "settings",
            ],
        )
        self.assertFalse(payload["features"]["security_scanner"]["interactive"])
        self.assertFalse(payload["features"]["legal_compliance"]["interactive"])
        self.assertFalse(payload["features"]["admin_panel"]["interactive"])
        self.assertFalse(payload["features"]["user_panel"]["interactive"])
        self.assertTrue(payload["features"]["legal_assistant"]["interactive"])

    def test_full_stage_makes_part_b_features_interactive(self):
        self.app.config["PROJECT_STAGE"] = "full"

        payload = self.client.get("/api/project-config").get_json()

        self.assertEqual(payload["stage"], "full")
        for feature in ("security_scanner", "legal_compliance", "admin_panel", "user_panel"):
            self.assertTrue(payload["features"][feature]["interactive"])


if __name__ == "__main__":
    unittest.main()
