"""Ingestion API routes."""

import os
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.loan_application import LoanApplication
from app.models.agent_memo import AgentMemo
from app.services.ingestion_service import ingest_pdf
from app.orchestration import run_workflow

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/upload")
def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Upload PDF → extract financials → create loan → run war-room workflow → return decision."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF file required")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # --- Step 1: existing ingestion (parse PDF, extract, store IngestedDocument) ---
    try:
        extracted = ingest_pdf(content=content, file_name=file.filename, db=db)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    financials = extracted.model_dump()

    # --- Step 2: create LoanApplication from extracted data ---
    company_name = os.path.splitext(file.filename)[0]
    has_compliance_issues = bool(extracted.compliance_keywords)

    loan = LoanApplication(
        company_name=company_name,
        industry="—",  # not available from PDF; placeholder
        requested_amount=0,  # actual loan amount not in PDF; set after review
        extracted_financials=financials,
        status="Pending",
        workflow_state="INGESTED",
        compliance_flag=has_compliance_issues,
    )
    db.add(loan)
    db.flush()  # assign loan.id before workflow

    # --- Step 3: run full agent orchestration workflow ---
    try:
        loan = run_workflow(loan, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {e}") from e

    # --- Step 4: build response ---
    memos = (
        db.query(AgentMemo)
        .filter(AgentMemo.loan_id == loan.id)
        .order_by(AgentMemo.created_at)
        .all()
    )

    return {
        "loan_id": str(loan.id),
        "company_name": loan.company_name,
        "status": loan.status,
        "final_score": loan.final_score,
        "confidence_score": loan.confidence_score,
        "compliance_flag": loan.compliance_flag,
        "workflow_state": loan.workflow_state,
        "extracted_financials": loan.extracted_financials,
        "agent_memos": [
            {
                "agent_type": m.agent_type,
                "content": m.content,
                "risk_score": m.risk_score,
            }
            for m in memos
        ],
    }
