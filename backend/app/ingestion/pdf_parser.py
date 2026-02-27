"""PDF text extraction using PyMuPDF."""

import fitz  # PyMuPDF


def extract_text_from_pdf(content: bytes) -> str:
    """Extract raw text from PDF bytes."""
    doc = fitz.open(stream=content, filetype="pdf")
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n".join(parts).strip()
