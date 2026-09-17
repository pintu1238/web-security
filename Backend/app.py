import json
import os
import re
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, Response, jsonify, request, send_file, send_from_directory
from werkzeug.exceptions import HTTPException

import knowledge
import assistant
import scanning
import storage
from templates import TITLES, render_document


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend" / "web"
PROFILE_KEYS = {
    "business_name", "owner", "email", "website", "business_type", "address", "notifications"
}
TASK_CATEGORIES = {"Legal", "Security", "Operations"}
TASK_PRIORITIES = {"high", "medium", "low"}
TASK_STATUSES = {"pending", "completed"}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PROJECT_PAGES = [
    "dashboard",
    "scanner",
    "compliance",
    "assistant",
    "documents",
    "knowledge",
    "admin",
    "user",
    "settings",
]
PROJECT_FEATURES = {
    "security_scanner": "Security scanner",
    "legal_compliance": "Legal compliance",
    "admin_panel": "Admin panel",
    "user_panel": "User panel",
    "legal_assistant": "Legal assistant",
    "document_studio": "Document studio",
    "knowledge_base": "Knowledge base",
}


class ApiError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _json_object():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object.")
    return payload


def _only_keys(payload, allowed):
    unknown = sorted(set(payload) - set(allowed))
    if unknown:
        raise ApiError(f"Unsupported field: {unknown[0]}.")


def _text(value, field, *, required=True, maximum=200):
    if not isinstance(value, str):
        raise ApiError(f"{field} must be a string.")
    value = value.strip()
    if required and not value:
        raise ApiError(f"{field} is required.")
    if len(value) > maximum:
        raise ApiError(f"{field} must be {maximum} characters or fewer.")
    return value


def _iso_date(value, field="due_date", nullable=False):
    if nullable and value is None:
        return None
    value = _text(value, field, maximum=10)
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ApiError(f"{field} must use YYYY-MM-DD format.") from error


def _validate_profile(payload):
    _only_keys(payload, PROFILE_KEYS)
    if not payload:
        raise ApiError("Provide at least one setting to update.")
    values = {}
    for key, value in payload.items():
        if key == "notifications":
            if not isinstance(value, bool):
                raise ApiError("notifications must be true or false.")
            values[key] = value
            continue
        required = key in {"business_name", "business_type"}
        maximum = {
            "business_name": 150,
            "owner": 150,
            "email": 254,
            "website": 2048,
            "business_type": 100,
            "address": 1000,
        }[key]
        values[key] = _text(value, key, required=required, maximum=maximum)
    if "email" in values and values["email"] and not EMAIL_PATTERN.fullmatch(values["email"]):
        raise ApiError("email must be a valid email address.")
    if "website" in values and values["website"]:
        raw_website = values["website"]
        try:
            website = urlsplit(raw_website)
            hostname = website.hostname
            website.port
            if hostname:
                hostname.encode("idna")
        except (UnicodeError, ValueError) as error:
            raise ApiError("website must be a valid http(s) URL.") from error
        if (
            website.scheme not in {"http", "https"}
            or not website.netloc
            or not hostname
            or website.username is not None
            or website.password is not None
            or any(character.isspace() for character in raw_website)
        ):
            raise ApiError("website must be a valid http(s) URL.")
    return values


def _scan_report(scan):
    lines = [
        "NitiShield Passive Website Security Assessment",
        "",
        f"Website: {scan['url']}",
        f"Created: {scan['created_at']}",
        f"Score: {scan['score']}/100",
        f"Checks passed: {scan['checks_passed']} of {scan['checks_total']}",
        "",
        "Scope: Passive HTTP response and security-header checks only. This is not an active vulnerability scan.",
        "",
        "Findings",
    ]
    if not scan["findings"]:
        lines.append("No missing protections were identified by these limited passive checks.")
    for finding in scan["findings"]:
        lines += [
            "",
            f"- {finding['title']} ({finding['severity']})",
            f"  {finding['description']}",
            f"  Recommendation: {finding['recommendation']}",
        ]
    return "\n".join(lines) + "\n"


def create_app(test_config=None):
    flask_app = Flask(__name__, static_folder=None)
    flask_app.config.from_mapping(
        WORKSPACE_DB=os.environ.get("NITISHIELD_DB", str(BACKEND_DIR / "data" / "workspace.db")),
        LEGAL_DOCUMENTS_DIR=str(BACKEND_DIR / "legal_documents"),
        MAX_CONTENT_LENGTH=11 * 1024 * 1024,
        CHAT_BASE_URL=os.environ.get("NITISHIELD_CHAT_URL", "http://127.0.0.1:11434"),
        CHAT_MODEL=os.environ.get("NITISHIELD_CHAT_MODEL", "qwen2.5:1.5b"),
        CHAT_TRANSLATION_MODEL=os.environ.get("NITISHIELD_TRANSLATION_MODEL"),
        PROJECT_STAGE=os.environ.get("NITISHIELD_PROJECT_STAGE", "part_a"),
    )
    if test_config:
        flask_app.config.update(test_config)
    project_stage = str(flask_app.config.get("PROJECT_STAGE", "part_a")).strip().lower()
    if project_stage not in {"part_a", "full"}:
        project_stage = "part_a"
    flask_app.config["PROJECT_STAGE"] = project_stage
    db_path = Path(flask_app.config["WORKSPACE_DB"]).expanduser()
    if not db_path.is_absolute():
        db_path = PROJECT_DIR / db_path
    db_path = db_path.resolve()
    flask_app.config["WORKSPACE_DB"] = str(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    Path(flask_app.config["LEGAL_DOCUMENTS_DIR"]).mkdir(parents=True, exist_ok=True)
    storage.initialize(db_path)

    def database_path():
        return flask_app.config["WORKSPACE_DB"]

    def legal_directory():
        return flask_app.config["LEGAL_DOCUMENTS_DIR"]

    def knowledge_catalog(uploaded=None):
        return storage.sync_knowledge(database_path(), knowledge.list_documents(legal_directory()), uploaded)

    @flask_app.after_request
    def avoid_stale_workspace_data(response):
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @flask_app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({"error": str(error)}), error.status

    @flask_app.errorhandler(413)
    def handle_too_large(_error):
        return jsonify({"error": "Uploaded file is too large."}), 413

    @flask_app.errorhandler(404)
    def handle_not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found."}), 404
        return jsonify({"error": "Page not found."}), 404

    @flask_app.errorhandler(Exception)
    def handle_unexpected(error):
        if isinstance(error, HTTPException):
            return jsonify({"error": error.description}), error.code
        flask_app.logger.exception("Unexpected server error", exc_info=error)
        return jsonify({"error": "An unexpected server error occurred."}), 500

    @flask_app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @flask_app.get("/assets/<path:asset_path>")
    def assets(asset_path):
        return send_from_directory(FRONTEND_DIR, asset_path)

    @flask_app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @flask_app.get("/api/project-config")
    def project_config():
        """Describe the presentation stage without changing stored workspace data.

        Part A keeps every frontend screen visible while reserving selected
        workflows for the Part B implementation. This endpoint is a UI
        capability hint, not an authorization boundary; authenticated,
        role-aware checks belong in the Part B backend.
        """
        interactive = flask_app.config["PROJECT_STAGE"] == "full"
        part_b_features = {"security_scanner", "legal_compliance", "admin_panel", "user_panel"}
        return jsonify(
            {
                "stage": flask_app.config["PROJECT_STAGE"],
                "pages": PROJECT_PAGES,
                "features": {
                    name: {
                        "label": label,
                        "interactive": interactive if name in part_b_features else True,
                    }
                    for name, label in PROJECT_FEATURES.items()
                },
            }
        )

    @flask_app.get("/api/settings")
    def get_settings():
        return jsonify(storage.get_profile(database_path()))

    @flask_app.put("/api/settings")
    def put_settings():
        values = _validate_profile(_json_object())
        return jsonify(storage.update_profile(database_path(), values))

    @flask_app.get("/api/tasks")
    def get_tasks():
        return jsonify(storage.list_tasks(database_path()))

    @flask_app.post("/api/tasks")
    def post_task():
        payload = _json_object()
        _only_keys(payload, {"title", "category", "priority", "due_date"})
        title = _text(payload.get("title"), "title", maximum=200)
        category = _text(payload.get("category"), "category", maximum=30)
        priority = _text(payload.get("priority"), "priority", maximum=20).lower()
        if category not in TASK_CATEGORIES:
            raise ApiError("category must be Legal, Security, or Operations.")
        if priority not in TASK_PRIORITIES:
            raise ApiError("priority must be high, medium, or low.")
        due_date = _iso_date(payload.get("due_date"), nullable=True)
        task = storage.create_task(
            database_path(),
            {"title": title, "category": category, "priority": priority, "due_date": due_date},
        )
        return jsonify(task), 201

    @flask_app.patch("/api/tasks/<int:task_id>")
    def patch_task(task_id):
        payload = _json_object()
        _only_keys(payload, {"status"})
        status = _text(payload.get("status"), "status", maximum=20).lower()
        if status not in TASK_STATUSES:
            raise ApiError("status must be pending or completed.")
        task = storage.update_task_status(database_path(), task_id, status)
        if not task:
            raise ApiError("Task not found.", 404)
        return jsonify(task)

    @flask_app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        if not storage.delete_task(database_path(), task_id):
            raise ApiError("Task not found.", 404)
        return jsonify({"ok": True})

    @flask_app.get("/api/scans")
    def get_scans():
        return jsonify(storage.list_scans(database_path()))

    @flask_app.post("/api/scans")
    def post_scan():
        payload = _json_object()
        _only_keys(payload, {"url", "authorized"})
        if payload.get("authorized") is not True:
            raise ApiError("Explicit authorization is required before assessing a website.")
        url = _text(payload.get("url"), "url", maximum=2048)
        try:
            assessment = scanning.scan_website(url)
        except scanning.ScanValidationError as error:
            raise ApiError(str(error), 400) from error
        except scanning.ScanResolutionError as error:
            raise ApiError(str(error), 422) from error
        except scanning.ScanFetchError as error:
            raise ApiError(str(error), 502) from error
        return jsonify(storage.save_scan(database_path(), url, assessment)), 201

    @flask_app.get("/api/scans/<int:scan_id>/report")
    def download_scan_report(scan_id):
        scan = storage.get_scan(database_path(), scan_id)
        if not scan:
            raise ApiError("Scan not found.", 404)
        return Response(
            _scan_report(scan),
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename=nitishield-scan-{scan_id}.txt"},
        )

    @flask_app.get("/api/knowledge")
    def get_knowledge():
        return jsonify(knowledge_catalog())

    @flask_app.post("/api/knowledge")
    def post_knowledge():
        try:
            record = knowledge.save_upload(legal_directory(), request.files.get("file"))
        except FileExistsError as error:
            raise ApiError(str(error), 409) from error
        except knowledge.KnowledgeError as error:
            raise ApiError(str(error), 400) from error
        knowledge_catalog(uploaded=record)
        return jsonify({key: value for key, value in record.items() if not key.startswith("_")}), 201

    @flask_app.get("/api/knowledge/<document_id>/download")
    def download_knowledge(document_id):
        if not re.fullmatch(r"[0-9a-f]{16}", document_id):
            raise ApiError("Knowledge document not found.", 404)
        record = knowledge.find_document(legal_directory(), document_id)
        if not record:
            raise ApiError("Knowledge document not found.", 404)
        return send_file(
            record["_path"], mimetype="application/pdf", as_attachment=True,
            download_name=record["file_name"], conditional=True,
        )

    @flask_app.get("/api/assistant/status")
    def assistant_status():
        return jsonify(assistant.status(flask_app.config))

    @flask_app.post("/api/search")
    def search():
        payload = _json_object()
        _only_keys(payload, {"question", "document_id", "language"})
        question = _text(payload.get("question"), "question", maximum=2000)
        document_id = payload.get("document_id")
        if document_id is not None:
            if not isinstance(document_id, str) or not re.fullmatch(r"[0-9a-f]{16}", document_id):
                raise ApiError("document_id must identify a PDF in your library.")
            if not knowledge.find_document(legal_directory(), document_id):
                raise ApiError("Knowledge document not found.", 404)
        language = payload.get("language")
        if language is not None and (not isinstance(language, str) or language not in {"English", "नेपाली", "Hindi"}):
            raise ApiError("language must be English, नेपाली, or Hindi.")
        revision = storage.chat_revision(database_path())
        response = assistant.answer(
            legal_directory(), question, storage.list_conversations(database_path())[-6:],
            flask_app.config, document_id, language,
        )
        source = 'local_documents' if response['results'] or response['mode'] in {'no_sources', 'clarification'} else 'conversation' if response['mode'] == 'conversation' else 'general_knowledge'
        context = {key: response.get(key) for key in ('mode', 'language')}
        context['source'] = source
        saved = storage.save_conversation(database_path(), question, response["answer"], response["results"], revision, context)
        if saved is None:
            raise ApiError("Conversation history was cleared while this answer was pending. Send the question again to start a new conversation.", 409)
        return jsonify({"id": saved, "question": question, "source": source, **response})

    @flask_app.get("/api/conversations")
    def get_conversations():
        return jsonify(storage.list_conversations(database_path()))

    @flask_app.delete("/api/conversations")
    def delete_conversations():
        storage.clear_conversations(database_path())
        return jsonify({"ok": True})

    @flask_app.delete("/api/conversations/<int:conversation_id>")
    def delete_conversation(conversation_id):
        if not storage.delete_conversation(database_path(), conversation_id):
            raise ApiError("Conversation not found.", 404)
        return jsonify({"ok": True})

    @flask_app.get("/api/documents")
    def get_documents():
        return jsonify(storage.list_documents(database_path()))

    @flask_app.get("/api/documents/<int:document_id>")
    def get_document(document_id):
        document = storage.get_document(database_path(), document_id, include_content=True)
        if not document:
            raise ApiError("Document not found.", 404)
        return jsonify(document)

    @flask_app.delete("/api/documents/<int:document_id>")
    def delete_document(document_id):
        if not storage.delete_document(database_path(), document_id):
            raise ApiError("Document not found.", 404)
        return jsonify({"ok": True})

    @flask_app.post("/api/documents")
    def post_document():
        payload = _json_object()
        fields = {"type", "business_name", "owner", "address", "effective_date"}
        _only_keys(payload, fields)
        document_type = _text(payload.get("type"), "type", maximum=40)
        if document_type not in TITLES:
            raise ApiError("type must be privacy_policy, employment_agreement, nda, or incident_response.")
        values = {
            "type": document_type,
            "business_name": _text(payload.get("business_name"), "business_name", maximum=150),
            "owner": _text(payload.get("owner"), "owner", maximum=150),
            "address": _text(payload.get("address"), "address", maximum=1000),
            "effective_date": _iso_date(payload.get("effective_date"), "effective_date"),
        }
        title, content = render_document(
            document_type=values["type"],
            business_name=values["business_name"],
            owner=values["owner"],
            address=values["address"],
            effective_date=values["effective_date"],
        )
        return jsonify(storage.save_document(database_path(), values, title, content)), 201

    @flask_app.get("/api/documents/<int:document_id>/download")
    def download_document(document_id):
        document = storage.get_document(database_path(), document_id, include_content=True)
        if not document:
            raise ApiError("Document not found.", 404)
        filename = f"{document['type'].replace('_', '-')}-{document_id}.txt"
        return send_file(
            BytesIO(document["content"].encode("utf-8")),
            mimetype="text/plain; charset=utf-8",
            as_attachment=True,
            download_name=filename,
        )

    def dashboard_payload():
        return {
            "profile": storage.get_profile(database_path()),
            "tasks": storage.list_tasks(database_path()),
            "scans": storage.list_scans(database_path()),
            "documents": storage.list_documents(database_path()),
            "conversations": storage.list_conversations(database_path()),
            "knowledge": knowledge_catalog(),
            "activity": storage.list_activity(database_path()),
            "stats": storage.stats(database_path()),
        }

    @flask_app.get("/api/dashboard")
    def dashboard():
        return jsonify(dashboard_payload())

    @flask_app.get("/api/export")
    def export_data():
        payload = dashboard_payload()
        payload["documents"] = storage.list_documents(database_path(), include_content=True)
        payload["conversations"] = storage.list_conversations(database_path())
        payload["exported_at"] = storage.now_iso()
        payload["source_files"] = "PDF metadata is included in knowledge. Download original PDFs using each entry's url."
        return Response(
            json.dumps(payload, ensure_ascii=False, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=nitishield-export.json"},
        )

    return flask_app


app = create_app()


if __name__ == "__main__":
    if os.name == "nt":
        # Windows SO_REUSEADDR permits two development servers on one port,
        # which can leave the browser connected to an older app instance.
        from werkzeug.serving import ThreadedWSGIServer
        ThreadedWSGIServer.allow_reuse_address = False
        ThreadedWSGIServer.allow_reuse_port = False
    try:
        port = int(os.environ.get("PORT", "8501"))
    except ValueError:
        port = 8501
    bind_address = os.environ.get("NITISHIELD_HOST", "127.0.0.1")
    app.run(host=bind_address, port=port, debug=False, use_reloader=False)
