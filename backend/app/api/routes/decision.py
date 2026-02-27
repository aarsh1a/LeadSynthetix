"""Decision Memo API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.loan_application import LoanApplication
from app.services.decision_memo_service import generate_decision_memo_pdf

router = APIRouter(prefix="/decision", tags=["decision"])


@router.get("/{loan_id}/memo/pdf")
def download_decision_memo_pdf(
    loan_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    """Generate and download Decision Memo as PDF."""
    loan = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")

    pdf_bytes = generate_decision_memo_pdf(loan)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in (loan.company_name or "loan"))
    filename = f"decision-memo-{safe_name}-{loan_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
