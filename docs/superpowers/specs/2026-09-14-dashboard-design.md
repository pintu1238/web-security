# NitiShield professional workspace

Upgrade the existing Nepali SME legal and cybersecurity app in place. The user has authorized immediate implementation and asked for speed; routine design and execution decisions are delegated to us.

Use Flask to serve a new responsive HTML/CSS/JavaScript frontend at `/`, with no frontend build dependency. Keep the original Streamlit app available. Use a deep navy sidebar, off-white canvas, emerald accent, crisp typography, custom inline SVG icons and accessible controls. Pages: overview, security assessment, compliance, legal assistant, documents, knowledge base, settings.

All displayed business metrics derive from persisted SQLite state. Initial checklist items are explicitly starter recommendations, not verified legal obligations. No fabricated scan history, security score, AI generation, or legal verification. Security assessment is a passive HTTPS/header check against an explicitly authorized public website. Legal answers return source excerpts from local PDFs without requiring an embedding model download. Draft documents are practical templates with business fields and downloadable text. Persist tasks, settings, scans, generated documents and conversation history. Provide loading, empty, success and recoverable error states.

Bind locally by default. Limit upload sizes, sanitize filenames, reject invalid inputs, prevent scans reaching private network destinations, and render user text safely. Preserve existing config edits and databases. Verify API behavior with isolated databases and exercise the major frontend flows in a browser at desktop and mobile widths.
