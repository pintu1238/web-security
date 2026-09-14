import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pymupdf
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
import knowledge


def pdf_bytes(*pages):
    with pymupdf.open() as document:
        for text in pages:
            page = document.new_page()
            page.insert_textbox((40, 40, 550, 800), text, fontsize=10)
        return document.tobytes()


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.pdfs = self.root / 'pdfs'
        self.pdfs.mkdir()
        (self.pdfs / 'Leave policy.pdf').write_bytes(pdf_bytes(
            'Employees shall be entitled to eighteen days of paid annual leave per year. '
            'Leave requests must be submitted to a manager at least seven days in advance.',
            'Unused annual leave may be carried forward, subject to a maximum of five days.'
        ))
        (self.pdfs / 'Computer rules.pdf').write_bytes(pdf_bytes(
            'Unauthorized access to a computer system is prohibited. '
            'An offender may face imprisonment of up to three years or a fine of up to two hundred thousand rupees, or both.'
        ))
        self.app = create_app({'TESTING': True, 'WORKSPACE_DB': self.root / 'workspace.db',
                               'LEGAL_DOCUMENTS_DIR': self.pdfs,
                               'CHAT_MODEL': 'test-model', 'CHAT_BASE_URL': 'http://127.0.0.1:11434'})
        self.client = self.app.test_client()

    def model_response(self, answer):
        return Mock(status_code=200, json=lambda: {'message': {'role': 'assistant', 'content': answer}, 'done': True})

    @patch('requests.post')
    def test_generates_answer_from_pdf_and_saves_it(self, post):
        post.return_value = self.model_response('You get 18 days of paid leave each year. Ask your manager at least a week ahead. [1]')
        result = self.client.post('/api/search', json={'question': 'How much paid leave do I get?'}).get_json()
        self.assertIn('You get 18 days', result['answer'])
        self.assertNotIn('relevant excerpt(s)', result['answer'])
        self.assertEqual(result['mode'], 'generated')
        self.assertEqual(result['results'][0]['metadata']['law_name'], 'Leave policy')
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['messages'][0]['role'], 'system')
        self.assertIn('eighteen days', payload['messages'][-1]['content'])
        saved = self.client.get('/api/conversations').get_json()
        self.assertEqual(saved[-1]['answer'], result['answer'])

    @patch('requests.post')
    def test_followup_keeps_subject_and_recent_conversation(self, post):
        post.return_value = self.model_response('You get 18 days of paid leave. [1]')
        self.client.post('/api/search', json={'question': 'How much annual leave do I get?'})
        post.return_value = self.model_response('That means you can take 18 paid days off each year. [1]')
        result = self.client.post('/api/search', json={'question': 'Explain that simply'}).get_json()
        self.assertTrue(result['results'])
        self.assertEqual(result['results'][0]['metadata']['law_name'], 'Leave policy')
        messages = post.call_args.kwargs['json']['messages']
        self.assertTrue(any(m['role'] == 'user' and 'annual leave' in m['content'] for m in messages[:-1]))
        self.assertIn('18 paid days', result['answer'])

    @patch('requests.post')
    def test_new_topic_does_not_reuse_previous_document(self, post):
        post.return_value = self.model_response('You get 18 days. [1]')
        self.client.post('/api/search', json={'question': 'How much annual leave do I get?'})
        post.return_value = self.model_response('Unauthorized access is prohibited. [1]')
        result = self.client.post('/api/search', json={'question': 'What happens if someone hacks a computer?'}).get_json()
        self.assertTrue(result['results'])
        self.assertEqual(result['results'][0]['metadata']['law_name'], 'Computer rules')

    @patch('requests.post')
    def test_selected_pdf_is_used_for_summary_and_excludes_other_documents(self, post):
        doc = next(d for d in knowledge.list_documents(self.pdfs) if d['title'] == 'Leave policy')
        post.return_value = self.model_response('You get 18 paid days off, and can carry over up to five unused days. [1] [2]')
        result = self.client.post('/api/search', json={'question': 'Summarize this PDF', 'document_id': doc['id']})
        self.assertEqual(result.status_code, 200)
        results = result.get_json()['results']
        self.assertEqual({r['metadata']['law_name'] for r in results}, {'Leave policy'})
        self.assertEqual({r['metadata']['page_number'] for r in results}, {1, 2})

    @patch('requests.post')
    def test_uploaded_pdf_can_immediately_answer_questions(self, post):
        uploaded = self.client.post('/api/knowledge', data={'file': (io.BytesIO(pdf_bytes(
            'The warranty period is twenty four months from the date of purchase.'
        )), 'Warranty.pdf')}, content_type='multipart/form-data')
        self.assertEqual(uploaded.status_code, 201)
        post.return_value = self.model_response('Your warranty lasts two years from purchase. [1]')
        result = self.client.post('/api/search', json={'question': 'How long is my warranty?', 'document_id': uploaded.get_json()['id']}).get_json()
        self.assertIn('two years', result['answer'])
        self.assertIn('twenty four months', result['results'][0]['text'])

    @patch('requests.post')
    def test_missing_evidence_does_not_invent_an_answer(self, post):
        result = self.client.post('/api/search', json={'question': 'According to the PDFs, what is the maritime lobster quota?'}).get_json()
        self.assertEqual(result['results'], [])
        self.assertEqual(result.get('mode'), 'no_sources')
        post.assert_not_called()

    @patch('requests.post', side_effect=requests.ConnectionError('private server details'))
    def test_model_failure_is_explicit_and_preserves_sources(self, post):
        result = self.client.post('/api/search', json={'question': 'What is the annual leave policy?'}).get_json()
        self.assertEqual(result.get('mode'), 'unavailable')
        self.assertTrue(result['results'])
        self.assertNotIn('private server details', result['answer'])
        self.assertIn('AI', result['answer'])

    @patch('requests.post')
    def test_empty_or_malformed_model_output_is_not_a_success(self, post):
        for payload in ({'message': {'content': ''}}, {'message': None}, [], {'error': 'internal details'}):
            with self.subTest(payload=payload):
                post.return_value = Mock(status_code=200, json=lambda: payload)
                result = self.client.post('/api/search', json={'question': 'What is the annual leave policy?'}).get_json()
                self.assertEqual(result.get('mode'), 'unavailable')

    @patch('requests.post')
    def test_model_reasoning_is_never_shown_as_the_answer(self, post):
        for output in ('Internal reasoning about what to answer.</think>\nYou get 18 paid days off. [1]',
                       '<think>Internal reasoning</think>\nYou get 18 paid days off. [1]'):
            post.return_value = self.model_response(output)
            result = self.client.post('/api/search', json={'question': 'How much annual leave do I get?'}).get_json()
            self.assertEqual(result['answer'], 'You get 18 paid days off. [1]')

    @patch('requests.post')
    def test_truncated_model_output_is_not_a_finished_answer(self, post):
        post.return_value = Mock(json=lambda: {'message': {'content': 'You get 18 days, provided that'}, 'done': True, 'done_reason': 'length'})
        result = self.client.post('/api/search', json={'question': 'How much annual leave do I get?'}).get_json()
        self.assertEqual(result['mode'], 'unavailable')

    @patch('requests.post')
    def test_plain_wording_preserves_amounts_conditions_and_negation(self, post):
        post.return_value = self.model_response("You're entitled to 18 days of leave per year. Unused leave may not be carried forward. A fine not exceeding 200,000 rupees may apply. [1]")
        result = self.client.post('/api/search', json={'question': 'Explain the annual leave rules simply'}).get_json()
        self.assertIn('You get 18 days of leave a year.', result['answer'])
        self.assertIn('may not be carried forward', result['answer'])
        self.assertIn('up to 200,000 rupees may apply', result['answer'])

    @patch('requests.post')
    def test_explicit_quote_is_not_reworded(self, post):
        quote = 'Employees are entitled to eighteen days of leave per year. [1]'
        post.return_value = self.model_response(quote)
        result = self.client.post('/api/search', json={'question': 'Quote the exact wording about annual leave'}).get_json()
        self.assertEqual(result['answer'], quote)

    def test_invalid_or_missing_document_does_not_search_all_documents(self):
        for document_id, status in [('invalid', 400), ('a' * 16, 404)]:
            result = self.client.post('/api/search', json={'question': 'What is leave?', 'document_id': document_id})
            self.assertEqual(result.status_code, status)

    def test_invalid_language_is_a_client_error(self):
        for language in ([], {}, 7):
            response = self.client.post('/api/search', json={'question': 'What is leave?', 'language': language})
            self.assertEqual(response.status_code, 400)

    @patch('requests.post')
    def test_repeated_followups_keep_the_original_evidence(self, post):
        post.return_value = self.model_response('You get 18 days of paid leave. [1]')
        self.client.post('/api/search', json={'question': 'How much annual leave do I get?'})
        for question in ('Explain that simply', 'Give me an example', 'Why?', 'In simple words?', 'Explain it again'):
            result = self.client.post('/api/search', json={'question': question}).get_json()
            self.assertEqual(result.get('mode'), 'generated', question)
            self.assertEqual(result['results'][0]['metadata']['law_name'], 'Leave policy')

    @patch('requests.post')
    def test_followup_after_unanswered_question_does_not_reuse_old_subject(self, post):
        post.return_value = self.model_response('You get 18 days of leave. [1]')
        self.client.post('/api/search', json={'question': 'How much annual leave do I get?'})
        self.client.post('/api/search', json={'question': 'According to the PDFs, what is the maritime lobster quota?'})
        result = self.client.post('/api/search', json={'question': 'Explain that simply'}).get_json()
        self.assertEqual(result['results'], [])

    @patch('requests.post')
    def test_explain_new_topic_does_not_pin_old_document(self, post):
        post.return_value = self.model_response('You get 18 days of leave. [1]')
        self.client.post('/api/search', json={'question': 'How much annual leave do I get?'})
        post.return_value = self.model_response('Unauthorized access is prohibited. [1]')
        result = self.client.post('/api/search', json={'question': 'Explain unauthorized computer access'}).get_json()
        self.assertEqual(result['results'][0]['metadata']['law_name'], 'Computer rules')

    @patch('requests.post')
    def test_explicit_new_subject_overrides_incidental_followup_words(self, post):
        for question in ('Is it illegal to hack a computer?', 'Give me an example of computer hacking'):
            with self.subTest(question=question):
                self.client.delete('/api/conversations')
                post.return_value = self.model_response('You get 18 days of leave. [1]')
                self.client.post('/api/search', json={'question': 'How much annual leave do I get?'})
                post.return_value = self.model_response('Unauthorized computer access is prohibited. [1]')
                result = self.client.post('/api/search', json={'question': question}).get_json()
                self.assertEqual(result['results'][0]['metadata']['law_name'], 'Computer rules')

    @patch('requests.get')
    def test_status_reports_missing_model_without_exposing_connection_details(self, get):
        get.return_value = Mock(json=lambda: {'models': []})
        result = self.client.get('/api/assistant/status').get_json()
        self.assertFalse(result['ready'])
        get.return_value = Mock(json=lambda: {'models': [{'name': 'test-model'}]})
        self.assertTrue(self.client.get('/api/assistant/status').get_json()['ready'])
        get.side_effect = requests.ConnectionError('private configuration')
        result = self.client.get('/api/assistant/status').get_json()
        self.assertFalse(result['ready'])
        self.assertNotIn('private configuration', str(result))


class RetrievalTests(unittest.TestCase):
    def test_everyday_personal_information_question_finds_confidentiality_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'Rules.pdf').write_bytes(pdf_bytes(
                'Breach of confidentiality: A person given access to confidential records shall not disclose them without permission.',
                'An information technology tribunal shall administer the law. The law member chairs the tribunal.'
            ))
            results = knowledge.search(directory, 'How does the law protect my personal information?')
            self.assertTrue(results)
            self.assertEqual(results[0]['metadata']['page_number'], 1)

    def test_nepali_words_keep_combining_marks_and_match_english_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'Rules.pdf').write_bytes(pdf_bytes('Digital signatures identify the signer. Privacy safeguards personal data. A penalty may apply.'))
            for question in ('विद्युतीय हस्ताक्षर', 'गोपनीयता', 'सजाय'):
                with self.subTest(question=question):
                    self.assertTrue(knowledge.search(directory, question))

    def test_relevant_late_paragraph_is_not_lost_to_first_match_on_page(self):
        with tempfile.TemporaryDirectory() as directory:
            text = ('The annual report contains background information. ' * 30 +
                    '\nAnnual leave entitlement is eighteen paid days per year.')
            Path(directory, 'Policy.pdf').write_bytes(pdf_bytes(text))
            results = knowledge.search(directory, 'annual leave entitlement')
            self.assertTrue(results)
            self.assertIn('eighteen paid days', results[0]['text'])

    def test_keyword_matches_whole_words_not_substrings(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'Notes.pdf').write_bytes(pdf_bytes('This document describes a fine collection of refined architecture.'))
            self.assertEqual(knowledge.search(directory, 'define'), [])


if __name__ == '__main__':
    unittest.main()
