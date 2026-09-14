# NitiShield Dashboard Implementation Plan

**Goal:** Deliver a professional, usable frontend connected to persistent backend actions.
**Architecture:** Same-origin Flask JSON API and static web app; SQLite workspace storage isolated from the existing legal metadata store.
**Tech Stack:** Flask, SQLite, PyMuPDF, requests, vanilla JavaScript and CSS.
**Spec:** `docs/superpowers/specs/2026-09-14-dashboard-design.md`

## Global constraints

Preserve existing user edits. Use the current checkout on `codex/professional-dashboard`. No paid services or model downloads. Keep existing Streamlit source. Do not manufacture assessment results. All pages and actions must have usable error and empty states. Changes remain uncommitted for user review.

## Task 1: Persistent backend

Owner: backend implementer. Requirements and exact API contracts are in `docs/superpowers/plans/backend-brief.md`. Add isolated integration tests first and observe failures. Implement persistence, public-site passive assessment, PDF retrieval, template generation and settings. Run `.venv/Scripts/python.exe -m unittest discover -s Backend/tests -v` with `PYTHONPATH=Backend`. Report tests and limitations in `docs/superpowers/plans/backend-report.md`.

## Task 2: Professional frontend

Owner: primary agent. Create `frontend/web/index.html`, `styles.css`, `app.js`. Consume Task 1 contracts. Build responsive shell with seven views, full navigation, global search, notification panel, modal forms, upload, download, filtering and backend mutations. Use accessible labels and safe text escaping. Verify syntax and exercise actual flows in the browser.

## Task 3: Integration and review

Run isolated API tests and browser flows for task completion, settings persistence, legal search, template download, invalid and real assessments, upload, navigation and responsive layout. Review changes independently and fix material issues. Update README with one-command startup and truthful product limitations. Leave a running preview and open it in Codex.

## Progress

- [x] Inspect repository and preserve existing modifications.
- [x] Establish design and API boundary.
- [x] Backend and integration tests (16 new API tests plus the existing config test).
- [x] Frontend and browser verification (12 browser checks; desktop and mobile screenshots inspected).
- [x] Independent review; fixed asset routing, empty-checklist persistence, chat chronology and navigation lifecycle, address limits and malformed URL errors.
- [x] README startup instructions and local preview.

Test artifacts are generated under the ignored `test-results/` directory. Browser checks use disposable state and deterministic network fixtures; a separate read-only fetch also exercised the scanner against a public example website. Existing unrelated Turso database work was preserved.
