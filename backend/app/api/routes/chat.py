"""Chat API route - ask questions about a loan decision."""

import uuid
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.loan_application import LoanApplication
from app.models.agent_memo import AgentMemo
from app.services.llm_service import LLMService

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """User chat message."""

    loan_id: str
    message: str
    history: list[dict[str, str]] = []  # [{"role": "user"|"assistant", "content": "..."}]


class ChatResponse(BaseModel):
    """Assistant reply."""

    reply: str


SYSTEM_PROMPT = """You are an AI lending analyst assistant for the LendSynthetix platform.
You have access to the loan application data and all agent memos below.
Answer questions about the loan decision, agent reasoning, risk factors, compliance status, 
and financial metrics. Be direct, cite specific agent opinions and scores when relevant.
If the user asks about something not covered in the data, say so.

When explaining the decision:
- The final score formula is: 0.4*sales - 0.4*risk (or 0.3*sales - 0.3*risk + 0.2*(mod-50) when moderator was involved)
- Threshold for approval is 20
- Confidence is derived from abs(sales_score - risk_score) — lower variance = higher confidence
"""


def _build_context(loan: LoanApplication, memos: list[AgentMemo]) -> str:
    """Build context string from loan data and memos."""
    lines = [
        f"Company: {loan.company_name}",
        f"Industry: {loan.industry}",
        f"Requested Amount: ${loan.requested_amount:,.0f}" if loan.requested_amount else "",
        f"Status: {loan.status}",
        f"Final Score: {loan.final_score}",
        f"Confidence: {loan.confidence_score}",
        f"Compliance Flag: {loan.compliance_flag}",
        f"Workflow State: {loan.workflow_state}",
        "",
        "Extracted Financials:",
        json.dumps(loan.extracted_financials or {}, indent=2),
        "",
        "Agent Memos:",
    ]
    for m in memos:
        lines.append(f"[{m.agent_type}] (score: {m.risk_score}): {m.content}")
    return "\n".join(lines)


@router.post("/", response_model=ChatResponse)
def chat_about_loan(
    req: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Chat about a specific loan decision. Uses LLM with loan context."""
    try:
        loan_uuid = uuid.UUID(req.loan_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid loan_id")

    loan = db.query(LoanApplication).filter(LoanApplication.id == loan_uuid).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    memos = (
        db.query(AgentMemo)
        .filter(AgentMemo.loan_id == loan.id)
        .order_by(AgentMemo.created_at)
        .all()
    )

    context = _build_context(loan, memos)

    # Build messages
    messages_for_prompt = f"""{SYSTEM_PROMPT}

--- LOAN CONTEXT ---
{context}
--- END CONTEXT ---

"""
    # Append conversation history
    for msg in req.history[-10:]:  # last 10 messages max
        role = msg.get("role", "user")
        content = msg.get("content", "")
        messages_for_prompt += f"\n{role.upper()}: {content}"

    messages_for_prompt += f"\nUSER: {req.message}\nASSISTANT:"

    llm = LLMService()
    reply = llm.complete_text(messages_for_prompt, max_tokens=600)

    if not reply:
        reply = (
            f"Based on the data, {loan.company_name} was **{loan.status}** "
            f"with a final score of {loan.final_score} "
            f"(threshold: 20) and confidence of "
            f"{(loan.confidence_score or 0) * 100:.0f}%."
        )

    return ChatResponse(reply=reply)
