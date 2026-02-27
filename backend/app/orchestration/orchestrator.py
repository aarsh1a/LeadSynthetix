"""Orchestrator - runs state machine, agents, audit logging."""

import math
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.loan_application import LoanApplication
from app.models.agent_memo import AgentMemo
from app.models.audit_log import AuditLog
from app.orchestration.states import WorkflowState
from app.agents import SalesAgent, RiskAgent, ComplianceAgent, ModeratorAgent
from app.agents.schemas import AgentResult
from app.services.llm_service import LLMService


def _audit(
    db: Session,
    loan_id: uuid.UUID,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Log step to AuditLog."""
    entry = AuditLog(loan_id=loan_id, event_type=event_type, details=details)
    db.add(entry)
    db.flush()


def _set_state(loan: LoanApplication, state: WorkflowState) -> None:
    loan.workflow_state = state.value


def _save_memo(
    db: Session,
    loan_id: uuid.UUID,
    agent_type: str,
    result: AgentResult,
) -> None:
    """Persist agent memo."""
    memo = AgentMemo(
        loan_id=loan_id,
        agent_type=agent_type,
        content=result.memo,
        risk_score=result.score,
    )
    db.add(memo)
    db.flush()


def _confidence_from_variance(scores: list[float]) -> float:
    """Compute confidence (0-1) from agent score variance. Lower variance = higher confidence."""
    if len(scores) < 2:
        return 1.0
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std = math.sqrt(variance)
    # Map std to confidence: std 0 -> 1, std 30+ -> ~0.3
    confidence = max(0.2, 1.0 - (std / 50))
    return round(confidence, 2)


def run_workflow(loan: LoanApplication, db: Session) -> LoanApplication:
    """
    Run state machine from current state to FINALIZED.
    Flow:
    1. All 3 agents generate initial memos.
    2. If compliance_flag == True -> auto reject.
    3. If |Sales - Risk| > 20 -> trigger Moderator.
    4. final_score = 0.4*sales - 0.4*risk
    5. >20 = Approved, else = Rejected
    6. confidence_score from variance between agents.
    """
    llm = LLMService()
    sales_agent = SalesAgent(llm)
    risk_agent = RiskAgent(llm)
    compliance_agent = ComplianceAgent(llm)
    moderator_agent = ModeratorAgent(llm)

    financials: dict[str, Any] = (loan.extracted_financials or {})
    if isinstance(financials, dict):
        financials = {k: v for k, v in financials.items() if v is not None}
    else:
        financials = {}

    # Start from INGESTED or current state
    state = WorkflowState(loan.workflow_state)
    _audit(db, loan.id, "WORKFLOW_START", {"state": state.value})

    # --- INITIAL_REVIEW: run 3 agents ---
    if state in (WorkflowState.INGESTED, WorkflowState.INITIAL_REVIEW):
        _set_state(loan, WorkflowState.INITIAL_REVIEW)
        _audit(db, loan.id, "STATE_TRANSITION", {"from": state.value, "to": "INITIAL_REVIEW"})
        state = WorkflowState.INITIAL_REVIEW

        sales_result = sales_agent.evaluate(financials)
        _save_memo(db, loan.id, "Sales", sales_result)
        _audit(db, loan.id, "AGENT_MEMO", {"agent": "Sales", "score": sales_result.score, "flags": sales_result.flags})

        risk_result = risk_agent.evaluate(financials)
        _save_memo(db, loan.id, "Risk", risk_result)
        _audit(db, loan.id, "AGENT_MEMO", {"agent": "Risk", "score": risk_result.score, "flags": risk_result.flags})

        compliance_result = compliance_agent.evaluate(financials)
        _save_memo(db, loan.id, "Compliance", compliance_result)
        _audit(db, loan.id, "AGENT_MEMO", {
            "agent": "Compliance",
            "score": compliance_result.score,
            "flags": compliance_result.flags,
        })

        # 2. If compliance_flag == true -> auto reject (flagged for compliance issues)
        if loan.compliance_flag:
            _set_state(loan, WorkflowState.FINALIZED)
            loan.status = "Rejected"
            loan.final_score = 0.0
            loan.confidence_score = 1.0
            _audit(db, loan.id, "AUTO_REJECT", {"reason": "compliance_flag true"})
            _audit(db, loan.id, "STATE_TRANSITION", {"to": "FINALIZED"})
            db.commit()
            return loan

        # 3. If |Sales - Risk| > 20 -> DEBATE (trigger Moderator)
        if abs(sales_result.score - risk_result.score) > 20:
            _set_state(loan, WorkflowState.DEBATE)
            _audit(db, loan.id, "STATE_TRANSITION", {
                "to": "DEBATE",
                "reason": "sales_risk_diff",
                "diff": abs(sales_result.score - risk_result.score),
            })
            state = WorkflowState.DEBATE

            agent_outputs = {
                "sales": sales_result.model_dump(),
                "risk": risk_result.model_dump(),
                "compliance": compliance_result.model_dump(),
            }
            moderator_result = moderator_agent.evaluate(financials, agent_outputs)
            _save_memo(db, loan.id, "Moderator", moderator_result)
            _audit(db, loan.id, "AGENT_MEMO", {
                "agent": "Moderator",
                "score": moderator_result.score,
                "flags": moderator_result.flags,
            })
            # Use moderator score for final (blended with sales/risk per formula)
            sales_for_final = sales_result.score
            risk_for_final = risk_result.score
        else:
            sales_for_final = sales_result.score
            risk_for_final = risk_result.score
            moderator_result = None

        # --- CONSENSUS ---
        _set_state(loan, WorkflowState.CONSENSUS)
        _audit(db, loan.id, "STATE_TRANSITION", {"to": "CONSENSUS"})

        # 4. final_score = 0.4*sales - 0.4*risk
        final_score = 0.4 * sales_for_final - 0.4 * risk_for_final
        loan.final_score = round(final_score, 2)
        _audit(db, loan.id, "FINAL_SCORE_CALC", {
            "formula": "0.4*sales - 0.4*risk",
            "sales": sales_for_final,
            "risk": risk_for_final,
            "final_score": loan.final_score,
        })

        # 5. Decision: >20 = Approved, else = Rejected
        loan.status = "Approved" if loan.final_score > 20 else "Rejected"
        _audit(db, loan.id, "DECISION", {"threshold": 20, "status": loan.status})

        # 6. confidence_score from variance
        scores = [sales_result.score, risk_result.score, compliance_result.score]
        if moderator_result:
            scores.append(moderator_result.score)
        loan.confidence_score = _confidence_from_variance(scores)
        _audit(db, loan.id, "CONFIDENCE_CALC", {"scores": scores, "confidence": loan.confidence_score})

        # --- FINALIZED ---
        _set_state(loan, WorkflowState.FINALIZED)
        _audit(db, loan.id, "STATE_TRANSITION", {"to": "FINALIZED"})
        _audit(db, loan.id, "WORKFLOW_COMPLETE", {"status": loan.status, "final_score": loan.final_score})

    db.commit()
    return loan
