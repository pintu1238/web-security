"""Optional real Ollama check for ordinary chat and a searchable Nepali PDF."""
import io
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Backend' / 'tests'))
from test_chat_conversation import nepali_pdf
from app import create_app


def main():
    report = []
    output = ROOT / 'test-results' / 'chat-languages-live.json'
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        client = create_app({'TESTING': True, 'WORKSPACE_DB': root / 'workspace.db',
                             'LEGAL_DOCUMENTS_DIR': root / 'pdfs'}).test_client()
        uploaded = client.post('/api/knowledge', data={'file': (io.BytesIO(nepali_pdf()), 'Nepali leave.pdf')})
        assert uploaded.status_code == 201
        document_id = uploaded.get_json()['id']
        for options in (
            {'question': 'tell me about this website'},
            {'question': 'how can you help me?'},
            {'question': 'What is photosynthesis?'},
            {'question': 'Explain that simply'},
            {'question': 'कर्मचारीले कति दिन बिदा पाउँछन्?', 'document_id': document_id},
            {'question': 'बिदा लिन के गर्नुपर्छ?', 'document_id': document_id, 'language': 'नेपाली'},
            {'question': 'बिदाको नियम के हो?', 'document_id': document_id, 'language': 'English'},
        ):
            print('QUESTION:', options['question'], flush=True)
            started = time.monotonic()
            response = client.post('/api/search', json=options)
            result = response.get_json()
            report.append({'request': options, **result, 'seconds': round(time.monotonic() - started, 2)})
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print(result['mode'], result['answer'], report[-1]['seconds'], flush=True)
            expected_translation_limit = options.get('language') == 'English'
            if expected_translation_limit:
                assert result['mode'] == 'translation_unavailable', result
                assert result['language'] == 'English' and result['results']
                continue
            assert response.status_code == 200 and result['mode'] in {'conversation', 'general', 'generated'}, result
            assert '<think>' not in result['answer']
            if 'document_id' in options:
                assert result['results'] and result['results'][0]['metadata']['document_id'] == document_id
                if result['language'] == 'नेपाली':
                    assert sum('\u0900' <= c <= '\u097f' for c in result['answer']) > 20
                    if 'कति दिन' in options['question']:
                        assert '१८' in result['answer'] or '18' in result['answer'] or 'अठार' in result['answer'], result
                    if 'लिन के' in options['question']:
                        assert 'सात' in result['answer'] or '७' in result['answer'] or '7' in result['answer'], result
                        assert 'तीन' not in result['answer'], result
                else:
                    assert '18' in result['answer'] or 'eighteen' in result['answer'].lower(), result
                    assert 'must take' not in result['answer'].lower(), result
            else:
                assert not result['results']
        print('Saved', output)


if __name__ == '__main__':
    main()
