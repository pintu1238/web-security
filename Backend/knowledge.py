import hashlib
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pymupdf
from werkzeug.utils import secure_filename


MAX_PDF_BYTES = 10 * 1024 * 1024
STOPWORDS = {
    "about", "after", "again", "also", "are", "and", "can", "could", "does",
    "for", "from", "have", "how", "into", "is", "its", "may", "must", "not",
    "our", "should", "that", "the", "their", "this", "was", "what", "when",
    "where", "which", "who", "will", "with", "would", "your",
    "please", "tell", "explain", "simply", "simple", "say", "says", "get",
    "much", "many", "give", "some", "pdf", "document", "documents", "according",
    "there", "these", "those", "they", "them", "about", "been", "than", "then",
    "law", "act", "section", "chapter",
}

# Small vocabulary bridge for everyday questions about the legal library.
CONCEPTS = (
    {"hack", "hacks", "hacking", "hacked", "unauthorized", "unauthorised", "access"},
    {"online", "electronic", "digital", "विद्युतीय"},
    {"punishment", "penalty", "penalties", "fine", "imprisonment", "offence", "offense"},
    {"holiday", "vacation", "leave", "बिदा", "बिदाको", "बिदामा", "छुट्टी"},
    {"request", "requests", "apply", "निवेदन", "आवेदन"},
    {"sign", "signature", "signatures", "signed", "हस्ताक्षर"},
    {"गोपनीयता", "privacy", "confidentiality", "confidential", "personal"},
    {"सजाय", "penalty", "punishment"},
)


class KnowledgeError(ValueError):
    pass


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _inspect_pdf(data):
    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            if document.page_count < 1:
                raise KnowledgeError("PDF must contain at least one page.")
            pages = [page.get_text("text").strip() for page in document]
    except KnowledgeError:
        raise
    except Exception as error:
        raise KnowledgeError("File must be a valid, parseable PDF.") from error
    if not any(pages):
        raise KnowledgeError("PDF must contain searchable text; image-only PDFs are not supported.")
    return pages


@lru_cache(maxsize=64)
def _read_record(path, size, modified_ns):
    # Size and nanosecond mtime invalidate cached extraction when a PDF changes.
    data = path.read_bytes()
    try:
        pages = _inspect_pdf(data)
    except KnowledgeError:
        return None
    document_id = _digest(data)[:16]
    return {
        "id": document_id,
        "title": re.sub(r"-[0-9a-f]{12}$", "", path.stem).replace("_", " "),
        "file_name": path.name,
        "pages": len(pages),
        "size": len(data),
        "url": f"/api/knowledge/{document_id}/download",
        "_path": path,
        "_pages": pages,
        "_digest": _digest(data),
    }


def _record(path):
    stat = path.stat()
    return _read_record(path.resolve(), stat.st_size, stat.st_mtime_ns)


def list_documents(directory, internal=False):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted(directory.glob("*.pdf"), key=lambda item: item.name.lower()):
        record = _record(path)
        if record:
            records.append(record)
    if internal:
        return records
    return [{key: value for key, value in record.items() if not key.startswith("_")} for record in records]


def find_document(directory, document_id):
    for record in list_documents(directory, internal=True):
        if record["id"] == document_id:
            return record
    return None


def save_upload(directory, uploaded_file):
    if uploaded_file is None or not uploaded_file.filename:
        raise KnowledgeError("A PDF file is required.")
    if Path(uploaded_file.filename).suffix.lower() != ".pdf":
        raise KnowledgeError("Only PDF files are accepted.")
    data = uploaded_file.read(MAX_PDF_BYTES + 1)
    if not data:
        raise KnowledgeError("PDF file cannot be empty.")
    if len(data) > MAX_PDF_BYTES:
        raise KnowledgeError("PDF file must be 10 MB or smaller.")
    _inspect_pdf(data)
    digest = _digest(data)
    for record in list_documents(directory, internal=True):
        if record["_digest"] == digest:
            raise FileExistsError("This PDF is already in the knowledge base.")
    safe_stem = Path(secure_filename(uploaded_file.filename)).stem or "document"
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", safe_stem).strip("-_")[:60] or "document"
    path = Path(directory) / f"{safe_stem}-{digest[:12]}.pdf"
    path.write_bytes(data)
    return find_document(directory, digest[:16])


def _keywords(question):
    # Combining marks belong to words in Nepali/Hindi and many other scripts.
    tokens = "".join(character if unicodedata.category(character)[0] in "LMN" else " "
                     for character in question.casefold()).split()
    return [token for token in tokens if (len(token) >= 3 or token.isdigit()) and token not in STOPWORDS]


def _chunks(directory, document_id=None):
    chunks = []
    for document in list_documents(directory, internal=True):
        if document_id and document["id"] != document_id:
            continue
        for page_number, text in enumerate(document["_pages"], start=1):
            text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
            words = text.split()
            for start in range(0, len(words), 112):
                excerpt = " ".join(words[start:start + 140])
                if not excerpt:
                    continue
                chunks.append({
                    "chunk_id": f"{document['id']}-page-{page_number}-{start}",
                    "text": excerpt,
                    "metadata": {
                        "document_id": document["id"],
                        "law_name": document["title"],
                        "page_number": page_number,
                        "file_name": document["file_name"],
                        "url": document["url"],
                    },
                    "retrieval_method": "bm25",
                })
                if start + 140 >= len(words):
                    break
    return chunks


def search(directory, question, limit=5, document_id=None, overview=False):
    chunks = _chunks(directory, document_id)
    if not chunks:
        return []
    if overview:
        # Spread a bounded overview over the PDF, including its final pages.
        count = min(limit, len(chunks))
        indexes = [round(i * (len(chunks) - 1) / max(1, count - 1)) for i in range(count)]
        return [{**chunks[i], "retrieval_method": "overview"} for i in indexes]
    original = set(_keywords(question))
    if not original:
        return []
    terms = set(original)
    for concept in CONCEPTS:
        if original & concept:
            terms.update(concept)
    frequencies = [Counter(_keywords(chunk["text"])) for chunk in chunks]
    average_length = sum(sum(counts.values()) for counts in frequencies) / len(chunks) or 1
    document_frequency = Counter(term for counts in frequencies for term in counts)
    ranked = []
    for chunk, counts in zip(chunks, frequencies):
        matched = terms & counts.keys()
        if not matched:
            continue
        length = sum(counts.values())
        score = 0.0
        for term in matched:
            frequency = counts[term]
            inverse_frequency = math.log(1 + (len(chunks) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            weight = 1.0 if term in original else 0.75
            score += weight * inverse_frequency * frequency * 2.5 / (frequency + 1.5 * (0.25 + 0.75 * length / average_length))
        # Prefer coverage of the actual question over a repeated common term.
        covered = original & counts.keys()
        for term in original - covered:
            if any(term in concept and concept & counts.keys() for concept in CONCEPTS):
                covered.add(term)
        score *= 1 + len(covered) / len(original)
        title_matches = original & set(_keywords(chunk["metadata"]["law_name"]))
        score += 0.15 * len(title_matches)
        ranked.append((score, chunk))
    ranked.sort(key=lambda item: -item[0])
    results, seen = [], set()
    for _, chunk in ranked:
        if chunk["text"] in seen:
            continue
        results.append(chunk)
        seen.add(chunk["text"])
        if len(results) >= limit:
            break
    return results


def current_passages(directory, previous_results, document_id=None):
    """Re-read follow-up evidence so removed/replaced PDFs cannot remain sources."""
    current = {chunk["chunk_id"]: chunk for chunk in _chunks(directory, document_id)}
    return [current[item["chunk_id"]] for item in previous_results if item["chunk_id"] in current]
