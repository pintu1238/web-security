"""Run the web app with disposable state for browser verification."""
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "Backend"))
test_root = Path(os.environ["NITISHIELD_TEST_DIR"])
os.environ["NITISHIELD_DB"] = str(test_root / "workspace.db")

from app import create_app
import scanning
import assistant
import json
import requests

# Keep the browser success path deterministic by replacing only the external
# network boundary. The real URL validation, header scoring and storage run.
original_resolve = scanning.resolve_public_addresses
original_fetch = scanning._fetch_once


def resolve_fixture(hostname, port):
    if hostname == "browser-fixture.example":
        return ["93.184.216.34"]
    return original_resolve(hostname, port)


def fetch_fixture(url, pinned_ip):
    if url == "https://browser-fixture.example":
        return scanning.FetchResponse(200, {"x-content-type-options": "nosniff"}, b"<!doctype html><title>Browser fixture</title>")
    return original_fetch(url, pinned_ip)


scanning.resolve_public_addresses = resolve_fixture
scanning._fetch_once = fetch_fixture

application = create_app({
    "WORKSPACE_DB": test_root / "workspace.db",
    "LEGAL_DOCUMENTS_DIR": test_root / "legal_documents",
    "TESTING": True,
})

# Replace only external inference for repeatable UI checks. Run with
# NITISHIELD_LIVE_AI=1 to exercise the installed Ollama model instead.
if os.environ.get("NITISHIELD_LIVE_AI") != "1":
    application.config.update(CHAT_MODEL="browser-fixture", CHAT_BASE_URL="http://model-fixture.invalid")
    original_post = requests.post
    original_get = requests.get

    def model_response(payload):
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(payload).encode("utf-8")
        return response

    def post_model(url, **kwargs):
        if url != "http://model-fixture.invalid/api/chat":
            return original_post(url, **kwargs)
        prompt = json.loads(kwargs["json"]["messages"][-1]["content"])
        source = prompt["sources"][0]
        return model_response({"message": {"role": "assistant", "content": f"Test inference: {source['passage']} [1]"}, "done": True, "done_reason": "stop"})

    def get_model(url, **kwargs):
        if url == "http://model-fixture.invalid/api/tags":
            return model_response({"models": [{"name": "browser-fixture"}]})
        return original_get(url, **kwargs)

    assistant.requests.post = post_model
    assistant.requests.get = get_model

application.run(host="127.0.0.1", port=int(os.environ.get("TEST_PORT", "5056")), debug=False, use_reloader=False)
