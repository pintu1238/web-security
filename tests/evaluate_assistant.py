"""Optional live-model smoke test; uses a disposable workspace and real Ollama.

Run: .venv/Scripts/python.exe tests/evaluate_assistant.py
Requires the configured Ollama model to have been downloaded already.
"""
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Backend'))


def main():
    report = []
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        os.environ['NITISHIELD_DB'] = str(root / 'default.db')
        from app import create_app

        pdfs = root / 'pdfs'
        pdfs.mkdir()
        for source in (ROOT / 'Backend' / 'legal_documents').glob('*.pdf'):
            shutil.copy2(source, pdfs / source.name)
        app = create_app({'TESTING': True, 'WORKSPACE_DB': root / 'workspace.db', 'LEGAL_DOCUMENTS_DIR': pdfs})
        client = app.test_client()
        status = client.get('/api/assistant/status').get_json()
        if not status['ready']:
            raise RuntimeError(status['message'])
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_textbox((40, 40, 550, 800),
                'Employees shall be entitled to eighteen days of paid annual leave per year. '
                'Leave requests must be submitted to a manager at least seven days in advance. '
                'Unused annual leave may be carried forward, subject to a maximum of five days.', fontsize=11)
            data = pdf.tobytes()
        uploaded = client.post('/api/knowledge', data={'file': (io.BytesIO(data), 'Staff leave.pdf')}, content_type='multipart/form-data')
        assert uploaded.status_code == 201
        document_id = uploaded.get_json()['id']
        questions = [
            {'question': 'How much paid leave do I get, and how do I request it?', 'document_id': document_id},
            {'question': 'Explain that simply', 'document_id': document_id},
            {'question': 'What happens if someone hacks my computer?'},
            {'question': 'According to the PDFs, what is the maritime lobster quota?'},
        ]
        for values in questions:
            started = time.monotonic()
            print('QUESTION:', values['question'], flush=True)
            response = client.post('/api/search', json=values)
            result = response.get_json()
            result['elapsed_seconds'] = round(time.monotonic() - started, 2)
            assert response.status_code == 200, result
            if 'lobster' in values['question']:
                assert result['mode'] == 'no_sources', result
            else:
                assert result['mode'] == 'generated', result
                assert result['answer'] and result['results'], result
                # Inline citations depend on model wording; the UI always shows
                # these real page references alongside the generated answer.
                assert all(source['metadata']['page_number'] >= 1 for source in result['results'])
                assert 'relevant excerpt(s)' not in result['answer']
                assert '<think>' not in result['answer'] and '</think>' not in result['answer']
                assert len(result['answer'].split()) < 180, 'Expected a concise conversational answer'
            if 'paid leave' in values['question']:
                assert '18' in result['answer'] or 'eighteen' in result['answer'].lower(), result
                assert '7' in result['answer'] or 'seven' in result['answer'].lower() or 'week' in result['answer'].lower(), result
            if values['question'] == 'Explain that simply':
                assert result['answer'] != report[-1]['answer'], 'A simplification should not repeat the previous answer verbatim'
            report.append(result)
            print(result['answer'], '\nSeconds:', result['elapsed_seconds'], flush=True)
        output = ROOT / 'test-results' / 'assistant-live.json'
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Saved', output, flush=True)


if __name__ == '__main__':
    main()
