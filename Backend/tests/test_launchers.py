"""Both Python entry points must serve the same real workspace."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]


class LauncherTests(unittest.TestCase):
    def test_python_entries_default_to_the_same_dashboard_port(self):
        # Intercept only the blocking server call; run the real entry points and
        # app initialization in fresh interpreters, without touching live ports.
        probe = """
import json, runpy, sys
from flask import Flask
def capture(app, **kwargs):
    print(json.dumps({'port': kwargs['port'], 'host': kwargs['host']}))
Flask.run = capture
sys.path.insert(0, sys.argv[2])
runpy.run_path(sys.argv[1], run_name='__main__')
"""
        with tempfile.TemporaryDirectory() as directory:
            env = {key: value for key, value in os.environ.items()
                   if key not in {"PORT", "NITISHIELD_HOST"}}
            env["NITISHIELD_DB"] = str(Path(directory) / "workspace.db")
            for entry in (ROOT / "Backend/app.py", ROOT / "frontend/app.py"):
                with self.subTest(entry=entry):
                    result = subprocess.run(
                        [sys.executable, "-c", probe, str(entry), str(ROOT / "Backend")],
                        cwd=entry.parent, env=env, capture_output=True, text=True, timeout=15,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout), {"port": 8501, "host": "127.0.0.1"})

    def test_relative_database_setting_is_independent_of_launch_folder(self):
        probe = """
import json, os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import app
app.PROJECT_DIR = Path(sys.argv[2])
os.environ['NITISHIELD_DB'] = 'shared.db'
workspace = app.create_app()
print(json.dumps({'database': str(workspace.config['WORKSPACE_DB'])}))
"""
        with tempfile.TemporaryDirectory() as directory:
            expected = Path(directory) / "shared.db"
            env = {**os.environ, "NITISHIELD_DB": str(expected)}
            for cwd in (Path(directory), Path(directory) / "Backend", Path(directory) / "frontend"):
                cwd.mkdir(exist_ok=True)
                with self.subTest(cwd=cwd):
                    result = subprocess.run(
                        [sys.executable, "-c", probe, str(ROOT / "Backend"), directory], cwd=cwd,
                        env=env, capture_output=True, text=True, timeout=15,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout)["database"], str(expected))

    def test_frontend_entry_reopens_the_workspace_created_by_backend(self):
        with tempfile.TemporaryDirectory() as directory:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            env = {**os.environ, "PORT": str(port), "NITISHIELD_HOST": "127.0.0.1",
                   "NITISHIELD_DB": str(Path(directory) / "workspace.db")}
            base = f"http://127.0.0.1:{port}"
            for entry in ("Backend/app.py", "frontend/app.py"):
                with self.subTest(entry=entry), tempfile.TemporaryFile() as log:
                    process = subprocess.Popen([sys.executable, str(ROOT / entry)], cwd=(ROOT / entry).parent,
                                               env=env, stdout=log, stderr=log)
                    try:
                        ready = False
                        for _ in range(100):
                            if process.poll() is not None:
                                break
                            try:
                                with urlopen(base + "/api/health", timeout=0.5) as response:
                                    ready = response.status == 200
                                if ready:
                                    break
                            except (URLError, OSError):
                                time.sleep(0.1)
                        self.assertTrue(ready, f"{entry} did not serve the real workspace API")
                        if entry.startswith("Backend"):
                            request = Request(base + "/api/settings", data=json.dumps({"business_name": "Restart proof"}).encode(),
                                              headers={"Content-Type": "application/json"}, method="PUT")
                            with urlopen(request, timeout=3) as response:
                                self.assertEqual(response.status, 200)
                            duplicate = subprocess.Popen([sys.executable, str(ROOT / entry)], cwd=ROOT,
                                                         env=env, stdout=log, stderr=log)
                            try:
                                try:
                                    code = duplicate.wait(timeout=15)
                                except subprocess.TimeoutExpired:
                                    self.fail("A second server accepted the same port instead of refusing stale/ambiguous service")
                                self.assertNotEqual(code, 0)
                                with urlopen(base + "/api/settings", timeout=3) as response:
                                    self.assertEqual(json.load(response)["business_name"], "Restart proof")
                            finally:
                                if duplicate.poll() is None:
                                    duplicate.terminate()
                                duplicate.wait(timeout=5)
                        else:
                            with urlopen(base + "/api/settings", timeout=3) as response:
                                self.assertEqual(json.load(response)["business_name"], "Restart proof")
                            with urlopen(base, timeout=3) as response:
                                self.assertIn(b"/assets/app.js", response.read())
                    finally:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
