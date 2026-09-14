# NitiShield AI

A professional security and compliance workspace for Nepali small and medium businesses. The responsive web interface and Flask API run together, with SQLite persistence and a local PDF knowledge base.

## Start the app

From the project folder, start the shared interface:

```powershell
.\start.ps1
```

Open **http://localhost:8501/#dashboard**. Use this same address in VS Code, Codex, and your browser. The frontend and backend are served together from the same workspace database; no separate frontend server is needed.

In **VS Code**, open this project folder and choose **Run and Debug > NitiShield** (F5) to start the app and open that address. **Terminal > Run Task > NitiShield: Start** runs the same PowerShell launcher. Run only one server at a time; if it is already running, just open the dashboard address.

Do not use `streamlit run app.py` for this project. If an old Streamlit terminal is still running, stop it with Ctrl+C first. On Windows, an old Streamlit server can occupy IPv6 port 8501 while Flask occupies IPv4 port 8501, causing `localhost` to show a different app.

For another device on your local network, use this computer's current network address with port 8501. It reaches the same app and data.

For a fresh setup:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r Backend\requirements-web.txt
.\start.ps1
```

The launcher accepts `-Port` and `-BindAddress` overrides. Direct Python entry points (`.venv\Scripts\python.exe Backend\app.py` and `.venv\Scripts\python.exe frontend\app.py`) also default to port **8501** and the same database. On macOS or Linux, use `.venv/bin/python Backend/app.py`. Direct Python startup is local-only unless `NITISHIELD_HOST=0.0.0.0` is set. `PORT` can explicitly select another port; leave it unset for the shared default.

Every normal launch uses `Backend/data/workspace.db`, regardless of the current folder. `NITISHIELD_DB` is an optional explicit override; relative paths are resolved from the project root, so launching from `Backend/` or `frontend/` does not create another database. Leave it unset to use the shared default.

## What works

- **Overview:** database metrics, task progress, recent activity (including PDF uploads and assistant answers), global search, notifications, and a downloadable workspace export. Navigation, search and reminders refresh from the backend so changes from another tab are visible.
- **Security scanner:** an authorised, passive assessment of a public website's HTTPS and five response-header protections (six checks total), with saved findings and downloadable reports. Private network destinations are rejected, including redirects to them.
- **Legal compliance:** add, complete, reopen, search, filter and remove checklist tasks. Changes persist across reloads and restarts.
- **Legal assistant:** get conversational answers grounded in your PDFs, with numbered page references. Choose one PDF or search the library, summarize selected passages, and ask follow-up questions. Conversation history is saved and can be cleared.
- **Document studio:** create, reopen, copy and download privacy policy, employment agreement, non-disclosure agreement, and incident response plan drafts using your saved business details.
- **Knowledge base:** upload searchable PDFs up to 10 MB, search the library, and open the original sources. The included Electronic Transactions Act PDF is available automatically.
- **Settings:** saved business profile, in-app reminder preferences, and data export.

The app needs no paid service, API key, embedding download, or frontend build step. AI answers use a local Ollama model; install it once as described below. The interface is `frontend/web/`. The former Streamlit demo has been retired: `.venv\Scripts\python.exe frontend\app.py` now starts the same database-backed application on port 8501. Use `start.ps1` for network access. Running the old file through Streamlit displays migration instructions instead of simulated results.

## Enable conversational PDF answers

Install [Ollama](https://ollama.com/download), keep it running, and download the default model once:

```powershell
ollama pull qwen2.5:1.5b
.\start.ps1
```

The model download is approximately 1 GB. The default is a small instruction model chosen for this CPU-only machine; larger installed instruction models can be configured below. Open the **Legal assistant**, choose a PDF in **Answer from**, and ask normally—for example, “What does this mean for my business?” Follow with “Explain that simply” or “Give me an example.” Use **Ask about it** in the knowledge base to select an uploaded PDF and prepare a summary request. Uploads become searchable immediately.

The first answer may take longer while the model loads. On a CPU, allow up to three minutes per answer. The assistant shows whether the model is ready. If Ollama is unavailable, it explains the problem and leaves the original sources accessible; it does not pretend excerpts are an AI answer.

To use another installed Ollama model or server, set these environment variables **before starting Flask** (a `.env` file is not automatically loaded):

```powershell
$env:NITISHIELD_CHAT_MODEL = "qwen2.5:1.5b"
$env:NITISHIELD_CHAT_URL = "http://127.0.0.1:11434"
.\start.ps1
```

The default runs locally: PDF passages and chat context are sent only to your local Ollama instance. Configuring a remote URL sends that context to that server. No credentials are required for local use.

Answers use overlapping PDF passages ranked with BM25 and a small everyday-language vocabulary bridge, recent conversation context, and explicit instructions to paraphrase supported facts and cite the pages. This follows document-grounding principles in [Anthropic’s contextual retrieval guidance](https://www.anthropic.com/engineering/contextual-retrieval), [Google’s prompt design guidance](https://ai.google.dev/gemini-api/docs/prompting-strategies), and [Ollama’s chat API](https://docs.ollama.com/api/chat). It does not reproduce those providers’ proprietary chatbots or claim equivalent accuracy. Long-document summaries cover selected passages, not necessarily every clause. Cross-language retrieval is limited to matching terms and the included vocabulary bridge.

## Data and scope

Workspace records are stored in `Backend/data/workspace.db`, separately from the legacy legal metadata and Chroma databases. Tasks, settings, scans, findings, generated document contents, conversations, activity and the PDF catalog are persisted in SQLite. Original PDF files are stored in `Backend/legal_documents/`; the catalog is synchronized with those files when read, including existing PDFs. JSON export includes full generated documents, chat history, findings, settings, tasks, activity and PDF metadata. Download original PDFs separately using their source links; the JSON export is not a binary PDF backup.

This is a **single-workspace application** without user accounts or multi-tenant isolation. `start.ps1` makes it accessible on the local network; direct `Backend/app.py` startup stays local-only unless `NITISHIELD_HOST` is set. The Flask development server is for development use; public deployment needs a production server and authentication.

Security assessments check a public HTTP response and are not a comprehensive vulnerability audit. Checklist items are starter recommendations, not verified legal obligations. AI explanations can make mistakes; check the cited PDF pages before relying on legal details. Document outputs are text templates requiring review and completion before use. Scanned image PDFs require text extraction elsewhere before upload.

## Verify

Run all backend, persistence and process-restart checks:

```powershell
.venv\Scripts\python.exe -m unittest discover -s Backend\tests -v
```

These suites keep PDF parsing, retrieval and persistence real, and replace only the external model request. For an optional end-to-end check using the installed Ollama model and a temporary PDF/workspace:

```powershell
.venv\Scripts\python.exe tests\evaluate_assistant.py
```

It checks an uploaded leave policy, a follow-up, the included legal PDF and an unsupported question, and writes answers plus timings to `test-results/assistant-live.json` for review.

The browser tests exercise UI actions against disposable SQLite databases and PDF directories, then inspect the stored records independently. The repeatable suites replace only external website responses and model inference with fixtures. They default to the installed Brave browser on Windows and require Playwright for Node:

```powershell
npm install --no-save playwright
node tests\browser-smoke.cjs
node tests\browser-integrity.cjs
```

For a separate Brave check using real Ollama answers, an uploaded PDF, a follow-up, browser reload and a real public HTTP assessment of example.com:

```powershell
node tests\browser-live-services.cjs
```

Set `BROWSER_EXECUTABLE` to use another browser binary, `PYTHON` to use another Python interpreter, `HEADLESS=1` to hide test windows, or `TEST_PORT` to choose a free port (defaults: 5056 smoke, 5057 integrity, 5058 live services). `PLAYWRIGHT_MODULE` can point at an existing Playwright installation. Screenshots and JSON check reports are written to the ignored `test-results/` folder. Live service checks require an installed Ollama model and internet access; unavailable services are reported as failures.
