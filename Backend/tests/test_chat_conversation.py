"""Regression cases for ordinary conversation and Nepali PDF questions."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pymupdf
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
import storage


def nepali_pdf():
    # Obtain PyMuPDF's bundled Devanagari font, then embed it with a Unicode
    # character map. Story's shaped glyph map does not round-trip this fixture.
    with pymupdf.open() as font_document:
        page = font_document.new_page()
        page.insert_htmlbox((40, 40, 550, 800), '<p>बिदा</p>')
        font = font_document.extract_font(page.get_fonts()[0][0])[3]
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_font(fontname='devanagari', fontbuffer=font)
        page.insert_textbox((40, 40, 550, 800),
                            'बिदाको नियम: कर्मचारीले वर्षमा १८ दिन तलबसहित बिदा पाउँछन्। '
                            'बिदा लिन सात दिन अगाडि निवेदन दिनुपर्छ।', fontname='devanagari', fontsize=12)
        assert 'बिदाको नियम' in page.get_text()
        return document.tobytes()


class ConversationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.client = create_app({'TESTING': True, 'WORKSPACE_DB': root / 'workspace.db',
                                  'LEGAL_DOCUMENTS_DIR': root / 'pdfs',
                                  'CHAT_MODEL': 'test-model'}).test_client()

    def ask(self, question, **options):
        response = self.client.post('/api/search', json={'question': question, **options})
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def upload_nepali(self):
        response = self.client.post('/api/knowledge', data={'file': (io.BytesIO(nepali_pdf()), 'Leave.pdf')})
        self.assertEqual(response.status_code, 201)
        return response.get_json()['id']

    @patch('requests.post')
    def test_website_and_help_questions_work_without_pdfs_or_model(self, post):
        for question in ('tell me about this website', 'how can you help me?',
                         'What is NitiShield?', 'What can you do?', 'Who are you?',
                         'How can you help me with PDFs?'):
            result = self.ask(question)
            self.assertEqual(result['mode'], 'conversation', question)
            self.assertIn('NitiShield', result['answer'])
            self.assertNotIn('could not find', result['answer'])
            self.assertEqual(result['results'], [])
            self.assertEqual(result['source'], 'conversation')
        post.assert_not_called()

    @patch('requests.post')
    def test_general_knowledge_uses_model_without_fake_pdf_sources(self, post):
        post.return_value = Mock(json=lambda: {'message': {'content': 'Plants use sunlight to make food. [1]'}})
        result = self.ask('What is photosynthesis?')
        self.assertEqual(result['mode'], 'general')
        self.assertEqual(result['source'], 'general_knowledge')
        self.assertEqual(result['results'], [])
        self.assertNotIn('[1]', result['answer'])
        self.assertIn('sunlight', result['answer'])
        self.assertNotIn('ONLY on the source passages', post.call_args.kwargs['json']['messages'][0]['content'])

    @patch('requests.post')
    def test_general_followup_keeps_context(self, post):
        post.return_value = Mock(json=lambda: {'message': {'content': 'Plants use sunlight to make food.'}})
        self.ask('What is photosynthesis?')
        self.ask('Explain that simply')
        messages = post.call_args.kwargs['json']['messages']
        self.assertTrue(any(m['role'] == 'user' and m['content'] == 'What is photosynthesis?' for m in messages))

    @patch('requests.post')
    def test_general_summary_does_not_summarize_an_unrelated_pdf(self, post):
        self.upload_nepali()
        post.return_value = Mock(json=lambda: {'message': {'content': 'Plants make food using sunlight.'}})
        self.ask('What is photosynthesis?')
        result = self.ask('Summarize that')
        self.assertEqual(result['mode'], 'general')
        self.assertEqual(result['results'], [])

    @patch('requests.post')
    def test_subject_question_starting_what_are_you_is_not_app_help(self, post):
        post.return_value = Mock(json=lambda: {'message': {'content': 'That depends on which law and location you mean.'}})
        result = self.ask('What are you allowed to do under employment law?')
        self.assertEqual(result['mode'], 'general')

    @patch('requests.post')
    def test_explicit_pdf_question_without_sources_does_not_use_general_knowledge(self, post):
        result = self.ask('According to my PDF, what is the maritime lobster quota?')
        self.assertEqual(result['mode'], 'no_sources')
        post.assert_not_called()

    @patch('requests.post', side_effect=requests.ConnectionError('private details'))
    def test_general_model_outage_does_not_claim_it_found_pdf_passages(self, post):
        result = self.ask('What is photosynthesis?')
        self.assertEqual(result['mode'], 'unavailable')
        self.assertNotIn('found relevant passages', result['answer'])
        self.assertNotIn('private details', result['answer'])

    @patch('requests.post')
    def test_nepali_pdf_is_retrieved_and_answer_language_is_explicit(self, post):
        document_id = self.upload_nepali()
        post.return_value = Mock(json=lambda: {'message': {'content': 'तपाईंले वर्षमा १८ दिन बिदा पाउनुहुन्छ। [1]'}})
        result = self.ask('कर्मचारीले कति दिन बिदा पाउँछन्?', document_id=document_id)
        self.assertEqual(result['mode'], 'generated')
        self.assertEqual(result['language'], 'नेपाली')
        self.assertTrue(result['results'])
        self.assertIn('१८', result['results'][0]['text'])
        payload = json.loads(post.call_args.kwargs['json']['messages'][-1]['content'])
        self.assertEqual(payload['reply_language'], 'नेपाली')
        self.assertEqual(post.call_args.kwargs['json']['model'], 'test-model')

    @patch('requests.post')
    def test_explicit_language_overrides_question_language(self, post):
        self.client.application.config['CHAT_TRANSLATION_MODEL'] = 'translation-test-model'
        document_id = self.upload_nepali()
        post.return_value = Mock(json=lambda: {'message': {'content': 'You get 18 paid days off a year. [1]'}})
        result = self.ask('बिदाको नियम के हो?', document_id=document_id, language='English')
        self.assertEqual(result['language'], 'English')
        payload = json.loads(post.call_args.kwargs['json']['messages'][-1]['content'])
        self.assertEqual(payload['reply_language'], 'English')
        self.assertEqual(post.call_args.kwargs['json']['model'], 'translation-test-model')

    @patch('requests.post')
    def test_unreliable_translation_is_not_presented_as_supported_pdf_facts(self, post):
        document_id = self.upload_nepali()
        result = self.ask('बिदाको नियम के हो?', document_id=document_id, language='English')
        self.assertEqual(result['mode'], 'translation_unavailable')
        self.assertEqual(result['language'], 'English')
        self.assertTrue(result['results'])
        post.assert_not_called()

    @patch('requests.post')
    def test_mixed_library_uses_only_sources_in_reply_language_without_translation_model(self, post):
        self.upload_nepali()
        with pymupdf.open() as document:
            page = document.new_page()
            page.insert_text((40, 40), 'Employees get eighteen days of annual leave.')
            response = self.client.post('/api/knowledge', data={'file': (io.BytesIO(document.tobytes()), 'English policy.pdf')})
        self.assertEqual(response.status_code, 201)
        post.return_value = Mock(json=lambda: {'message': {'content': 'You get eighteen days of leave. [1]'}})
        result = self.ask('How much leave do I get?', language='English')
        self.assertEqual(result['mode'], 'generated')
        self.assertEqual({item['metadata']['law_name'] for item in result['results']}, {'English policy'})
        payload = json.loads(post.call_args.kwargs['json']['messages'][-1]['content'])
        self.assertEqual(len(payload['sources']), 1)

    @patch('requests.post')
    def test_untagged_model_analysis_is_not_shown_as_a_finished_answer(self, post):
        post.return_value = Mock(json=lambda: {'message': {'content': "Okay, let's tackle this question. The user is asking about plants..."}})
        result = self.ask('What is photosynthesis?')
        self.assertEqual(result['mode'], 'unavailable')
        self.assertNotIn('The user is asking', result['answer'])

    @patch('requests.post')
    def test_pdf_help_followup_remains_a_conversation(self, post):
        self.ask('How can you help me with PDFs?')
        post.return_value = Mock(json=lambda: {'message': {'content': 'Pick a PDF and ask me about it.'}})
        result = self.ask('Explain that simply')
        self.assertEqual(result['mode'], 'general')
        saved = self.client.get('/api/conversations').get_json()
        self.assertEqual(saved[0]['source'], 'conversation')
        self.assertEqual(saved[0]['mode'], 'conversation')

    @patch('requests.post')
    def test_repeated_followups_cannot_turn_missing_pdf_evidence_into_general_claims(self, post):
        self.ask('According to my PDF, what is the maritime lobster quota?')
        for question in ('Explain that simply', 'Give me an example', 'Why?'):
            result = self.ask(question)
            self.assertEqual(result['mode'], 'no_sources')
        post.assert_not_called()

    def test_existing_conversation_database_is_migrated_without_losing_history(self):
        path = Path(self.client.application.config['WORKSPACE_DB']).parent / 'legacy.db'
        with storage.connect(path) as connection:
            connection.execute('CREATE TABLE conversations (id INTEGER PRIMARY KEY, question TEXT, answer TEXT, results_json TEXT, created_at TEXT)')
            connection.execute("INSERT INTO conversations VALUES (1, 'hello', 'Hi!', '[]', '2026-09-14')")
        storage.initialize(path)
        storage.initialize(path)
        self.assertEqual(storage.list_conversations(path)[0]['answer'], 'Hi!')

    @patch('requests.post')
    def test_english_leave_question_can_find_nepali_pdf(self, post):
        document_id = self.upload_nepali()
        post.return_value = Mock(json=lambda: {'message': {'content': 'तपाईंले वर्षमा १८ दिन बिदा पाउनुहुन्छ। [1]'}})
        result = self.ask('How much leave do I get?', document_id=document_id, language='नेपाली')
        self.assertEqual(result['mode'], 'generated')
        self.assertEqual(result['language'], 'नेपाली')
        self.assertIn('१८', result['results'][0]['text'])

    @patch('requests.post')
    def test_nepali_rephrasing_keeps_previous_evidence(self, post):
        document_id = self.upload_nepali()
        post.return_value = Mock(json=lambda: {'message': {'content': 'तपाईंले वर्षमा १८ दिन बिदा पाउनुहुन्छ। [1]'}})
        self.ask('कर्मचारीले कति दिन बिदा पाउँछन्?', document_id=document_id)
        for question in ('यसलाई सरल भाषामा बुझाउनुहोस्', 'अझ सजिलो भाषामा भन्नुहोस्', 'उदाहरण दिनुहोस्'):
            result = self.ask(question, document_id=document_id)
            self.assertEqual(result['mode'], 'generated', question)
            self.assertTrue(result['results'])

    @patch('requests.post')
    def test_natural_language_request_for_nepali_is_not_sent_as_english(self, post):
        post.return_value = Mock(json=lambda: {'message': {'content': 'बिरुवाले सूर्यको प्रकाशबाट खाना बनाउँछन्।'}})
        result = self.ask('Explain photosynthesis in Nepali')
        self.assertEqual(result['language'], 'नेपाली')

    @patch('requests.post')
    def test_nepali_app_help_and_missing_sources_are_localized(self, post):
        result = self.ask('तपाईंले कसरी सहयोग गर्न सक्नुहुन्छ?')
        self.assertEqual(result['mode'], 'conversation')
        self.assertIn('सहयोग', result['answer'])
        result = self.ask('यो PDF मा के छ?', language='नेपाली')
        self.assertEqual(result['mode'], 'no_sources')
        self.assertIn('भेटिनँ', result['answer'])
        post.assert_not_called()


if __name__ == '__main__':
    unittest.main()
