"""Ingestion API routes."""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.ingestion_service import ingest_pdf
from app.extraction.schemas import ExtractionResult

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/upload", response_model=ExtractionResult)
def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ExtractionResult:
    """Upload PDF, extract text, run regex + LLM extraction, store and return structured JSON."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF file required")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        return ingest_pdf(content=content, file_name=file.filename, db=db)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
