"""Ingestion service - upload, parse, extract, store."""

from sqlalchemy.orm import Session

from app.models.ingested_document import IngestedDocument
from app.ingestion.pdf_parser import extract_text_from_pdf
from app.extraction.extractor import extract
from app.extraction.schemas import ExtractionResult
from app.services.llm_service import LLMService


def ingest_pdf(
    content: bytes,
    file_name: str,
    db: Session,
) -> ExtractionResult:
    """Parse PDF, store raw text, extract financials, return structured result."""
    raw_text = extract_text_from_pdf(content)
    llm = LLMService()
    extracted = extract(raw_text, llm=llm)
    doc = IngestedDocument(
        raw_text=raw_text,
        file_name=file_name,
        extracted_data=extracted.model_dump(),
    )
    db.add(doc)
    db.commit()
    return extracted
