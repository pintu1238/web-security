# NitiShield AI

A professional security and compliance workspace for Nepali small and medium businesses. The responsive web interface and Flask API run together, with SQLite persistence and a local PDF knowledge base.

## Start the app

From the project folder, start the shared interface:

```powershell
.\start.ps1
```

## Project defense stages

The frontend includes every planned screen in both stages so the complete
product can be demonstrated during Part A. The default `part_a` stage keeps
Security Scanner, Legal Compliance, Admin Panel and User Panel controls in
preview mode; their forms and mutations are labelled as Part B while the
assistant, documents, knowledge base and settings remain interactive.

Start Part A with:

```powershell
.\start.ps1 -ProjectStage part_a
```

Use the full interactive stage when the Part B workflows are ready:

```powershell
.\start.ps1 -ProjectStage full
```

This stage setting changes presentation capabilities only. Authentication and
backend role checks will be added before the Admin and User panels are used for
real workspace access.

`start.ps1` waits until Flask is ready and then opens **http://localhost:8501/#dashboard** automatically in your default browser. Use this same address in VS Code, Codex, and your browser. The frontend and backend are served together from the same workspace database; no separate frontend server is needed. Use `.\start.ps1 -NoBrowser` when you only want the terminal server.

In **VS Code**, open this project folder and choose **Run and Debug > NitiShield** (F5) to start the app and open that address. **Terminal > Run Task > NitiShield: Start** runs the same PowerShell launcher. Run only one server at a time; if it is already running, just open the dashboard address.

Do not use `streamlit run app.py` for this project. If an old Streamlit terminal is still running, stop it with Ctrl+C first. On Windows, an old Streamlit server can occupy IPv6 port 8501 while Flask occupies IPv4 port 8501, causing `localhost` to show a different app.

For another device on your local network, use this computer's current network address with port 8501. It reaches the same app and data.

For a fresh setup:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r Backend\requirements-web.txt
.\start.ps1
```

The launcher accepts `-Port`, `-BindAddress`, `-ProjectStage` and `-NoBrowser` overrides. Direct Python entry points (`.venv\Scripts\python.exe Backend\app.py` and `.venv\Scripts\python.exe frontend\app.py`) also default to port **8501** and the same database. On macOS or Linux, use `.venv/bin/python Backend/app.py`. Direct Python startup is local-only unless `NITISHIELD_HOST=0.0.0.0` is set. `PORT` can explicitly select another port; leave it unset for the shared default.

Every normal launch uses `Backend/data/workspace.db`, regardless of the current folder. `NITISHIELD_DB` is an optional explicit override; relative paths are resolved from the project root, so launching from `Backend/` or `frontend/` does not create another database. Leave it unset to use the shared default.

## What works

- **Overview:** database metrics, task progress, recent activity (including PDF uploads and assistant answers), global search, notifications, and a downloadable workspace export. Navigation, search and reminders refresh from the backend so changes from another tab are visible.
- **Security scanner:** an authorised, passive assessment of a public website's HTTPS and five response-header protections (six checks total), with saved findings and downloadable reports. Private network destinations are rejected, including redirects to them.
- **Legal compliance:** add, complete, reopen, search, filter and remove checklist tasks. Changes persist across reloads and restarts.
- **Legal assistant:** ask everyday questions, get help with NitiShield, or get answers grounded in your PDFs with numbered page references. Choose a PDF for focused questions, summarize selected passages, and ask follow-ups. Select English, नेपाली or Hindi, or let Auto follow your question’s language. Conversation history is saved and can be cleared.
- **Document studio:** create, reopen, copy, download and delete privacy policy, employment agreement, non-disclosure agreement, and incident response plan drafts using your saved business details.
- **Knowledge base:** upload searchable PDFs up to 10 MB, search the library, and open the original sources. The included Electronic Transactions Act PDF is available automatically.
- **Settings:** saved business profile, in-app reminder preferences, and data export.

The app needs no paid service, API key, embedding download, or frontend build step. AI answers use a local Ollama model; install it once as described below. The interface is `frontend/web/`. The former Streamlit demo has been retired: `.venv\Scripts\python.exe frontend\app.py` now starts the same database-backed application on port 8501. Use `start.ps1` for network access. Running the old file through Streamlit displays migration instructions instead of simulated results.

## Enable conversational PDF answers

Install [Ollama](https://ollama.com/download), keep it running, and download the default model once:

```powershell
ollama pull qwen2.5:1.5b
.\start.ps1
```

The model is approximately 1 GB and runs locally. Open the **Legal assistant** and ask normally. “Tell me about this website” and “How can you help me?” work immediately, even without a model or PDF. Leave **Answer from** on Auto for general chat and library search, or choose a PDF to require an answer from that document. Use **Ask about it** in the knowledge base to prepare a summary. Uploads become searchable immediately.

For a Nepali PDF, ask in Nepali or select **Reply in → नेपाली**. Auto follows your question’s language, not the PDF’s language; you can also request a language in your question. An explicit selector choice takes precedence. Nepali/Hindi script detection is heuristic because they share Devanagari; choose the language explicitly when needed. Nepali PDF text must be searchable Unicode. Scanned pages need OCR, and PDFs with broken font-to-Unicode mappings may need conversion before upload. Cross-language retrieval uses a small vocabulary bridge rather than a multilingual embedding model.

**Translation limitation:** the installed small model answered the tested Nepali PDF questions in Nepali, but changed facts when translating Nepali passages into English. PDF answers in a different language are therefore declined by default, with original sources retained. To enable translation with another model you have installed and evaluated, set `NITISHIELD_TRANSLATION_MODEL` to its Ollama model name. App help and general chat can still use the selected language. This limitation is separate from whether the PDF text can be extracted.

The model loads on demand and releases memory after each answer on this CPU-only machine. Allow up to three minutes for generation; an optional translation model has a six-minute limit. App introductions and basic help are immediate. The assistant shows whether the model is downloaded. If Ollama is unavailable, it explains the problem and leaves the original sources accessible; it does not pretend excerpts are an AI answer.

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

For real ordinary-chat and Nepali PDF checks, run `.venv\Scripts\python.exe tests\evaluate_chat_languages.py`. This uses an actual searchable Nepali PDF and the local model, checks the leave amounts and notice period, checks that unsupported translation is declined, and saves answers in `test-results/chat-languages-live.json`. Source references remain available for checking the model’s answers.

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
