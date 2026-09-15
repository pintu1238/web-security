"""Response language selection and short, translated interface answers."""
import re


def resolve(question, selected=None):
    if selected:
        return selected
    if re.search(r'\b(in|into)\s+nepali\b|नेपालीमा', question, re.I):
        return 'नेपाली'
    if re.search(r'\b(in|into)\s+hindi\b|हिन्दी में|हिंदी में', question, re.I):
        return 'Hindi'
    if re.search(r'\b(in|into)\s+english\b|अंग्रेजीमा|अङ्ग्रेजीमा', question, re.I):
        return 'English'
    if re.search(r'[\u0900-\u097f]', question):
        # Devanagari is shared by Nepali and Hindi. The selector resolves ambiguity.
        return 'Hindi' if re.search(r'(?:^|\s)(क्या|है|हैं|मुझे|बताओ)(?:\s|[।?!]|$)', question) else 'नेपाली'
    return 'English'


TEXT = {
    'greeting': (
        'Namaste! Ask me a question, tell me what you need help with, or pick a PDF to discuss.',
        'नमस्ते! तपाईं के जान्न चाहनुहुन्छ? सामान्य प्रश्न सोध्नुहोस् वा कुनै PDF छानेर त्यसबारे कुरा गरौँ।',
        'नमस्ते! कोई सवाल पूछिए, बताइए आपको किस चीज़ में मदद चाहिए, या चर्चा के लिए कोई PDF चुनिए।'),
    'thanks': (
        'You’re welcome! You can ask a follow-up whenever you like.',
        'स्वागत छ! अरू केही जान्न मन लागे सोध्नुहोस्।',
        'आपका स्वागत है! कोई और सवाल हो तो पूछिए।'),
    'app': (
        'NitiShield helps you manage security and compliance for your business. You can check a public website’s HTTPS and security headers, track compliance tasks, create document drafts, and upload PDFs to ask questions about them. I can explain those features, answer everyday questions, and help you understand your documents in simple words.',
        'NitiShield ले तपाईंको व्यवसायको सुरक्षा र नियम पालनसम्बन्धी काममा सहयोग गर्छ। यहाँ वेबसाइटको HTTPS र सुरक्षा हेडर जाँच्न, कामको सूची राख्न, कागजातको मस्यौदा बनाउन र PDF अपलोड गरेर प्रश्न सोध्न सकिन्छ। म सामान्य प्रश्नको जवाफ दिन र कागजातका कुरा सरल भाषामा बुझाउन सहयोग गर्न सक्छु।',
        'NitiShield आपके व्यवसाय की सुरक्षा और नियमों के पालन से जुड़े कामों में मदद करता है। यहाँ वेबसाइट के HTTPS और सुरक्षा हेडर जाँच सकते हैं, कामों की सूची रख सकते हैं, दस्तावेज़ों के मसौदे बना सकते हैं और PDF अपलोड करके सवाल पूछ सकते हैं। मैं सामान्य सवालों के जवाब और दस्तावेज़ों की सरल व्याख्या दे सकता हूँ।'),
    'choose_pdf': (
        'Which PDF would you like me to summarize? Choose it from the document selector above, then send your question.',
        'कुन PDF को सारांश चाहनुहुन्छ? माथिको सूचीबाट त्यो PDF छानेर प्रश्न पठाउनुहोस्।',
        'किस PDF का सारांश चाहिए? ऊपर की सूची से उसे चुनकर अपना सवाल भेजिए।'),
    'no_sources': (
        'I could not find enough information in these PDFs to answer that reliably. Choose the relevant PDF or upload a document that covers it.',
        'यो प्रश्नको भरपर्दो जवाफ दिन पुग्ने जानकारी PDF मा भेटिनँ। सम्बन्धित PDF छान्नुहोस् वा यो विषय समेटिएको कागजात अपलोड गर्नुहोस्।',
        'इस सवाल का भरोसेमंद जवाब देने के लिए PDF में पर्याप्त जानकारी नहीं मिली। संबंधित PDF चुनिए या इस विषय का दस्तावेज़ अपलोड कीजिए।'),
    'unavailable': (
        'The local AI couldn’t finish an answer. Make sure Ollama is running and the model is downloaded, then try again.',
        'स्थानीय AI ले जवाफ तयार गर्न सकेन। Ollama चलिरहेको र मोडेल डाउनलोड भएको निश्चित गरेर फेरि प्रयास गर्नुहोस्।'),
    'sources_available': (
        'You can still read the relevant PDF passages below.',
        'तल PDF का सम्बन्धित अंश पढ्न सक्नुहुन्छ।'),
}


def text(key, language):
    return TEXT[key][{'English': 0, 'नेपाली': 1, 'Hindi': 2}[language]]


def instruction(language):
    if language == 'नेपाली':
        return '\nजवाफ नेपाली भाषामा मात्र दिनुहोस्। सोधिएको कुराको मात्र छोटो जवाफ दिनुहोस्। स्रोतका तथ्य, सङ्ख्या र समयावधि जस्ताको तस्तै राख्नुहोस्। जवाफका सबै सङ्ख्या स्रोतसँग मिलेको जाँच्नुहोस्। नपाएको कुरा नथप्नुहोस्।'

    return '\nWrite the answer in English.'
