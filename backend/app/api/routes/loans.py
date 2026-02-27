"""Loans API routes - list and detail."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.loan_application import LoanApplication
from app.models.agent_memo import AgentMemo

router = APIRouter(prefix="/loans", tags=["loans"])


def _loan_to_dict(loan: LoanApplication, memos: list[AgentMemo]) -> dict[str, Any]:
    """Serialise a loan + its memos to a JSON-safe dict."""
    return {
        "id": str(loan.id),
        "company_name": loan.company_name,
        "industry": loan.industry,
        "requested_amount": loan.requested_amount,
        "extracted_financials": loan.extracted_financials,
        "status": loan.status,
        "workflow_state": loan.workflow_state,
        "final_score": loan.final_score,
        "compliance_flag": loan.compliance_flag,
        "confidence_score": loan.confidence_score,
        "created_at": loan.created_at.isoformat() if loan.created_at else None,
        "agent_memos": [
            {
                "id": str(m.id),
                "agent_type": m.agent_type,
                "content": m.content,
                "risk_score": m.risk_score,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memos
        ],
    }


@router.get("/")
def list_loans(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return all loan applications (most recent first)."""
    loans = (
        db.query(LoanApplication)
        .order_by(LoanApplication.created_at.desc())
        .all()
    )
    result = []
    for loan in loans:
        memos = (
            db.query(AgentMemo)
            .filter(AgentMemo.loan_id == loan.id)
            .order_by(AgentMemo.created_at)
            .all()
        )
        result.append(_loan_to_dict(loan, memos))
    return result


@router.get("/{loan_id}")
def get_loan(loan_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return a single loan application with all agent memos."""
    loan = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")

    memos = (
        db.query(AgentMemo)
        .filter(AgentMemo.loan_id == loan.id)
        .order_by(AgentMemo.created_at)
        .all()
    )
    return _loan_to_dict(loan, memos)
