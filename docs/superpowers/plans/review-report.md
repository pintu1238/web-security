# NitiShield web workspace review

Reviewed 2026-09-14 against the dashboard design specification, backend brief, review-diff.txt, and current source. Read-only application review; no application source changed and no implementer tests rerun. Browser validation belongs to the root task. Findings below are static control-flow/contract findings, not claims of executed reproduction.

## Verdict

The implementation substantially covers the intended seven-page workspace and real persisted backend flows. It keeps model loading out of startup, derives metrics from SQLite, clearly labels starter recommendations and draft documents, escapes rendered business text, restricts PDF uploads, and pins resolved public addresses for website requests while validating redirects and TLS. The code has focused storage, scanning, retrieval, and template modules. Final acceptance should follow correction of the persistence and chat lifecycle issues below and the independent browser/test results.

## Findings

### P2 — Deleting every task is undone at the next application start

Location: `Backend/storage.py:128–134`.

`initialize()` seeds starter tasks whenever the task table is empty. A user can delete all six recommendations through the implemented UI, but restarting the application recreates them, changing the persisted checklist and dashboard metrics against the user's choices. Empty is a valid saved workspace state. Seed only when first initializing a workspace, using a durable initialization marker or the result of first creating its profile; do not infer first-run state from the task count.

### P2 — Returning to an in-flight conversation leaves its new form disabled

Location: `frontend/web/app.js:287` (also `:206` and `:276–286`).

Start a question, leave the assistant page, and return before the search finishes. `assistantView()` creates a new disabled input and submit button because `busyChat` is true. The pending request retains the old, detached form, and its `finally` only re-enables that old input; `handleForm` similarly restores only its old connected submit. The current assistant form stays disabled after completion, and the answer is written into the detached pending element. Update the current assistant view on completion, or target the live form and synchronize its displayed conversation from state; preserve the question/answer and restore both controls on failure as well.

### P2 — Persisted conversations reverse chronology on reload

Location: `Backend/storage.py:333` and `frontend/web/app.js:135–137,206`.

The API returns conversations newest first, but the UI renders them in supplied order, scrolls to the bottom, and appends new answers at the bottom. After two exchanges, leaving and returning to the assistant reverses their order and scrolls to the oldest exchange. Further replies are appended to an already reversed history. Normalize chat history to oldest first before rendering, either in the API query or at the frontend response boundary.

### P2 — A valid saved profile address can be rejected when creating its draft

Location: `Backend/app.py:336` and `frontend/web/app.js:217`.

Settings accept addresses up to 1000 characters and document forms permit and prefill the same length, but the document endpoint rejects addresses over 500. A valid 501–1000 character saved address makes the standard prefilled creation flow fail. Use one consistent address limit across saved settings, draft validation, and the form, preferably preserving the currently accepted profile length.

## Additional input handling observation

`Backend/app.py:95` calls `urlsplit()` without catching malformed-host `ValueError` (for example an unmatched IPv6 bracket). Those settings requests fall through to generic HTTP 500 instead of readable HTTP 400 validation. Catch parse errors and validate hostname/port as part of URL validation. This is lower impact than the four acceptance findings above.

## Scope and limitations

No concrete private-address SSRF bypass or unescaped user-text HTML sink was identified in this bounded review. This is not an exhaustive security audit. Header assessment is explicitly limited to a response snapshot and should retain that qualification. Source retrieval and templates are real local behavior, not generated legal advice. Existing legacy files outside this change were not reviewed or modified.

## Scoped re-review outcome — 2026-09-14

All five reported issues are addressed in the current source:

- `Backend/storage.py:114–133` seeds recommendations only when the settings row is newly inserted, preserving an intentionally empty task list across restarts.
- `frontend/web/app.js:278–298` reloads saved history after a successful search, resets the busy state, and reconstructs the current assistant form with enabled controls. Failed questions are restored to the live input. This addresses navigation during an in-flight question.
- `Backend/storage.py:333` returns conversations in ascending ID order, matching bottom-appended chat presentation and scrolling.
- `Backend/app.py:351` now accepts draft addresses up to 1000 characters, consistent with settings and the form.
- `Backend/app.py:94–112` catches malformed URL/host/port parsing and rejects invalid settings with the API validation error rather than an unexpected server error.

Re-review verdict: the original findings are closed; no remaining blocker identified within this scoped follow-up. Root reports 16 API tests plus config validation passing and 12 browser tests passing, including the reproduced-then-fixed pending-navigation regression, lifecycle/downloads, and mobile flows. Those tests were not rerun during this source-only re-review.
