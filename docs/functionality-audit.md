# Functionality and database audit

Checked on 14 September 2026 using the installed Brave browser, the Flask API, real SQLite databases, PDF uploads and source files. Mutating browser tests used disposable workspaces. The existing workspace was backed up before restart and its business records compared afterward.

## Feature-by-feature result

| Area | Data source | Verified behavior |
| --- | --- | --- |
| Overview | SQLite tasks, scans, findings, generated documents and activity | Unassessed baseline, computed metrics, task progress, quick navigation and JSON download. Data refreshes on navigation. |
| Global search | Current backend tasks, document records and PDF catalog; navigation labels are static UI | Finds current tasks and uploaded PDFs, opens the relevant screen and clears conflicting task filters. |
| Notifications | Current SQLite tasks and saved reminder preference | Shows pending tasks, respects disabled reminders, reloads changes made by another session. |
| Security scanner | Actual public HTTP/HTTPS response, then SQLite scans and findings | Authorization validation, private-address rejection, scoring, saved history, finding detail and report download. Real example.com request returned HTTP 201 and a 17/100 assessment during this run; fixture assessment returned 33/100 with four findings. |
| Legal compliance | SQLite tasks | Add, reload, complete, reopen, search, filter, remove and recompute dashboard progress. Starter tasks are initial database records. Deleting every task remains persisted. |
| Document studio | Template definitions plus saved profile; generated text stored in SQLite | All four templates create with business details, reopen after reload, copy text and download. Export includes full generated content. |
| Knowledge base | Original PDFs on disk, extracted text, SQLite metadata catalog | Real text-PDF upload, duplicate/invalid-file rejection, library search, original PDF download, scoped assistant questions and upload activity. Existing source files are synchronized into the catalog. |
| Legal assistant | Extracted PDF passages, local Ollama inference, SQLite conversation history | Uploaded-PDF answer and follow-up, source citations, reload persistence, source scoping, unavailable-model handling and history clearing. Real answers used the uploaded leave policy; both returned generated mode with citations. |
| Settings | SQLite settings | Profile fields persist, prefill document forms and scanner, reminder preference works, JSON export downloads. |
| Export | SQLite workspace records and PDF catalog | Includes profile, tasks, scans/findings, full generated document contents, conversation history, activity, PDF metadata and export time. Original PDF binaries remain separate downloads. |
| Navigation and recovery | Browser routing plus fresh backend responses | All seven pages checked at desktop and mobile sizes; no page overflow or JavaScript errors in the browser suites. Backend failure shows Retry, and successful retry reconnects. |
| Launchers | Shared Flask application and workspace database | Both Python entry points reopen the same persisted workspace, use port 8501 by default, and resolve relative database paths consistently. Duplicate Windows listeners are rejected. The old Streamlit demonstration is retired. |

## Problems corrected

- Dashboard, checklist, scanner history and settings could keep stale in-memory data after another session changed the database.
- Search and notifications did not refresh before reading workspace records; uploaded PDFs were absent from global search.
- A selected Completed filter could hide a pending task opened through search.
- Saved drafts could only be downloaded after closing their initial preview; they can now be reopened from stored content.
- JSON export omitted generated document text and conversation history.
- Uploaded PDFs had no persisted workspace catalog or upload activity.
- Clearing history could allow a pending answer to restore deleted rows; a database revision now prevents that write.
- Overlapping page/notification refreshes could render null or stale state; waiting callers now adopt the current refresh.
- Clear history stayed clickable in an active chat request, and a late history response could restore cleared messages onscreen; the button and response lifecycle are now guarded.
- The old Streamlit interface displayed simulated scans, fixed metrics and session-only settings; its Python entry now runs the connected web application.
- Windows could run multiple development servers on one port, leaving a browser on an older version; duplicate startup is now rejected.

## Verification and evidence

Commands (Playwright must be available, or set `PLAYWRIGHT_MODULE` to an installed package):

```powershell
.venv\Scripts\python.exe -m unittest discover -s Backend\tests -v
node tests\browser-smoke.cjs
node tests\browser-integrity.cjs
node tests\browser-live-services.cjs
node --check frontend\web\app.js
git diff --check
```

- Backend suite: **51 tests passed**. Covers validation, real PDF retrieval, SQLite persistence, exports, migrations, chat clear concurrency and process restart behavior.
- Brave smoke suite: **14 checks passed**. Independent SQL queries found six tasks, one assessment, four findings, four generated drafts, one conversation, two PDF catalog entries and activity records after UI actions.
- Brave integrity suite: **9 checks passed**, including overlapping requests and changes made by another browser session.
- Live Brave service check: **two generated Ollama answers**, conversation persistence after reload, and **one real public HTTP assessment** passed. The observed answer times were 5 and 11 seconds; timing depends on the model and machine load.
- After restart, all seven pages were opened again in Brave against the actual workspace on port 8501; current export fields, no-store headers and absence of browser JavaScript errors were verified.
- Code review identified two frontend timing defects; both were reproduced, fixed and re-reviewed without remaining findings in those fixes.
- Evidence files: `test-results/browser-smoke.json`, `browser-integrity.json`, `browser-live-services.json`, `backend-final.log`, `brave-real-ai.png`, `brave-real-scan.png` and the final live-page screenshots. Test results and the restart backup are local, ignored artifacts.

## What remains intentionally static

Navigation labels, help text, suggested questions, initial checklist recommendations and document template wording are product content. They do not pretend to be fetched business results. Template generation is a real persisted template operation; the scanner performs limited public-response checks; legal answers depend on the selected PDFs and local model. No external cloud database or multi-user account system was added.

Workspace database: `Backend/data/workspace.db`. Original sources: `Backend/legal_documents/`. The existing workspace's settings, tasks, scans, generated documents and conversations were unchanged by the restart.
