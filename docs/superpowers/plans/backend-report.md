# Backend implementation report

## Status

Implemented the Flask workspace backend described in `backend-brief.md`. The application now starts without importing the legacy embedding or Chroma search stack, serves `frontend/web/index.html` at `/`, serves its root-level files through `/assets/<path>`, and retains a global `app` alongside `create_app(test_config=None)`.

No frontend API contract shapes were changed. Settings limits were aligned with the frontend form: business name and owner 150 characters, email 254, website 2048, and address 1000. Generated documents accept those same business detail limits.

## Implemented behavior

- Persistent SQLite settings, tasks, scan history/findings, generated documents, activity, and conversations. The default path is `Backend/data/workspace.db`; `NITISHIELD_DB` or `WORKSPACE_DB` can override it.
- Six starter recommendations are inserted only when a workspace is first created. If a user deletes every task, reopening the workspace does not recreate them.
- Passive website assessment with explicit consent, HTTPS/header classification, TLS verification, public-address validation, DNS address pinning, per-redirect validation, a three-redirect limit, five-second connection/read timeout, and a 1 MB response cap.
- Actual local PDF discovery and secure downloads. Uploads accept parseable text PDFs up to 10 MB, generate safe content-derived names, and reject duplicate content and image-only files.
- Local PDF keyword excerpt retrieval with complete source metadata and chronological persisted conversation history. Greetings and no-result cases remain local and do not fabricate legal answers.
- Four practical text draft templates with interpolated business details and clear draft/review language.
- JSON API errors, downloadable text scan reports/document drafts, and a downloadable JSON workspace export.

## Verification evidence

Red runs were observed before implementation for the missing app factory, static asset route, frontend field limits, task reseeding, conversation ordering, document address limits, and malformed website URL handling.

Final scoped command:

```text
..\.venv\Scripts\python.exe -W error::ResourceWarning -m unittest tests.test_web_api tests.test_config_contract -v
Ran 17 tests in 7.345s
OK
```

Syntax verification:

```text
..\.venv\Scripts\python.exe -m py_compile app.py storage.py knowledge.py scanning.py templates.py tests\test_web_api.py
exit code 0
```

The tests use a separate temporary SQLite database and temporary legal-document directory for every case. PDF tests generate and parse real PDFs. Only outbound website network I/O is mocked; scan destination validation, redirects, persistence, scoring, reports, and response classification use production code.

## Operational notes and limits

- Start locally with `.venv\Scripts\python.exe Backend\app.py`. It binds to `127.0.0.1:5000` by default and accepts a numeric `PORT` override.
- Website assessment checks six response-level controls only: final HTTPS URL, CSP, HSTS, `X-Content-Type-Options`, frame protection, and `Referrer-Policy`. It does not perform an active vulnerability scan or certify security.
- PDF search is deterministic keyword matching, not semantic search. It does not OCR image-only documents or call external services.
- Knowledge records are derived from PDFs currently present in the configured directory, so deleting a source file removes it from the list and search results.
- `search_engine.py`, `database.py`, `config.py`, `requirements.txt`, `.env`, and the legacy databases were left untouched. The separately appearing Turso connection tests are outside this scoped verification and were not modified.
