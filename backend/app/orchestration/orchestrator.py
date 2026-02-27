"""Orchestrator - runs state machine, agents, audit logging."""

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


def _confidence_from_variance(sales_score: float, risk_score: float) -> float:
    """Compute confidence (0-1) from Sales vs Risk score variance.

    Confidence reflects consensus strength between Sales and Risk agents.
    Higher variance (disagreement) produces lower confidence.

    Mapping:
        variance  0-10  → 90-100% confidence
        variance 10-20  → 70-90%  confidence
        variance 20-40  → 50-70%  confidence
        variance  >40   → <50%    confidence (floor at 10%)
    """
    variance = abs(sales_score - risk_score)

    if variance <= 10:
        # Linear interpolation: 0 → 1.0, 10 → 0.9
        confidence = 1.0 - 0.01 * variance
    elif variance <= 20:
        # Linear interpolation: 10 → 0.9, 20 → 0.7
        confidence = 0.9 - 0.02 * (variance - 10)
    elif variance <= 40:
        # Linear interpolation: 20 → 0.7, 40 → 0.5
        confidence = 0.7 - 0.01 * (variance - 20)
    else:
        # Linear decay below 50%, floor at 10%
        confidence = max(0.1, 0.5 - 0.005 * (variance - 40))

    return round(confidence, 2)


def run_workflow(loan: LoanApplication, db: Session) -> LoanApplication:
    """
    Run state machine from current state to FINALIZED.
    Flow:
    1. All 3 agents generate initial memos (INITIAL_REVIEW).
    2. If compliance agent flags issues -> auto reject.
    3. If |Sales - Risk| > 20 -> multi-round DEBATE with Moderator.
    4. final_score:
       - no moderator: 0.4*sales - 0.4*risk
       - with moderator: 0.3*sales - 0.3*risk + 0.2*(mod-50)
    5. >20 = Approved, else = Rejected
    6. confidence_score from sales-risk variance.
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

        # 2. Compliance veto — use AGENT output, not just keyword flag
        compliance_veto = (
            loan.compliance_flag
            or compliance_result.score < 30
            or any(
                kw in f.lower()
                for f in compliance_result.flags
                for kw in ("aml", "grey list", "offshore", "sanction", "blocked")
            )
        )

        if compliance_veto:
            _set_state(loan, WorkflowState.FINALIZED)
            loan.status = "Rejected"
            loan.final_score = 0.0
            loan.confidence_score = 1.0
            loan.compliance_flag = True  # ensure persisted
            _audit(db, loan.id, "AUTO_REJECT", {
                "reason": "compliance_veto",
                "keyword_flag": loan.compliance_flag,
                "agent_score": compliance_result.score,
                "agent_flags": compliance_result.flags,
            })
            _audit(db, loan.id, "STATE_TRANSITION", {"to": "FINALIZED"})
            db.commit()
            return loan

        # -----------------------------------------------------------------
        # 3. DEBATE phase — multi-round argumentation (up to 2 rounds)
        # -----------------------------------------------------------------
        # Collect every memo across rounds for the full debate transcript.
        all_memos: list[dict[str, Any]] = [
            {"round": 0, "agent": "Sales", "score": sales_result.score,
             "memo": sales_result.memo, "flags": sales_result.flags},
            {"round": 0, "agent": "Risk", "score": risk_result.score,
             "memo": risk_result.memo, "flags": risk_result.flags},
            {"round": 0, "agent": "Compliance", "score": compliance_result.score,
             "memo": compliance_result.memo, "flags": compliance_result.flags},
        ]

        MAX_DEBATE_ROUNDS = 2
        moderator_result = None

        if abs(sales_result.score - risk_result.score) > 20:
            _set_state(loan, WorkflowState.DEBATE)
            _audit(db, loan.id, "STATE_TRANSITION", {
                "to": "DEBATE",
                "reason": "sales_risk_diff",
                "diff": abs(sales_result.score - risk_result.score),
            })
            state = WorkflowState.DEBATE

            for debate_round in range(1, MAX_DEBATE_ROUNDS + 1):
                _audit(db, loan.id, "DEBATE_ROUND_START", {"round": debate_round})

                # Each agent sees ALL prior memos and rebuts
                sales_result = sales_agent.evaluate(financials, prior_memos=all_memos)
                _save_memo(db, loan.id, "Sales", sales_result)
                _audit(db, loan.id, "AGENT_MEMO", {
                    "agent": "Sales", "round": debate_round,
                    "score": sales_result.score, "flags": sales_result.flags,
                })
                all_memos.append({
                    "round": debate_round, "agent": "Sales",
                    "score": sales_result.score, "memo": sales_result.memo,
                    "flags": sales_result.flags,
                })

                risk_result = risk_agent.evaluate(financials, prior_memos=all_memos)
                _save_memo(db, loan.id, "Risk", risk_result)
                _audit(db, loan.id, "AGENT_MEMO", {
                    "agent": "Risk", "round": debate_round,
                    "score": risk_result.score, "flags": risk_result.flags,
                })
                all_memos.append({
                    "round": debate_round, "agent": "Risk",
                    "score": risk_result.score, "memo": risk_result.memo,
                    "flags": risk_result.flags,
                })

                compliance_result = compliance_agent.evaluate(financials, prior_memos=all_memos)
                _save_memo(db, loan.id, "Compliance", compliance_result)
                _audit(db, loan.id, "AGENT_MEMO", {
                    "agent": "Compliance", "round": debate_round,
                    "score": compliance_result.score, "flags": compliance_result.flags,
                })
                all_memos.append({
                    "round": debate_round, "agent": "Compliance",
                    "score": compliance_result.score, "memo": compliance_result.memo,
                    "flags": compliance_result.flags,
                })

                # Moderator evaluates consensus
                moderator_result, consensus_reached = \
                    moderator_agent.evaluate_consensus(financials, all_memos)
                _save_memo(db, loan.id, "Moderator", moderator_result)
                _audit(db, loan.id, "AGENT_MEMO", {
                    "agent": "Moderator", "round": debate_round,
                    "score": moderator_result.score,
                    "flags": moderator_result.flags,
                    "consensus": consensus_reached,
                })
                all_memos.append({
                    "round": debate_round, "agent": "Moderator",
                    "score": moderator_result.score, "memo": moderator_result.memo,
                    "flags": moderator_result.flags,
                })

                _audit(db, loan.id, "DEBATE_ROUND_END", {
                    "round": debate_round,
                    "consensus": consensus_reached,
                    "score_spread": abs(sales_result.score - risk_result.score),
                })

                if consensus_reached:
                    _audit(db, loan.id, "CONSENSUS_REACHED", {"round": debate_round})
                    break

        # --- CONSENSUS ---
        _set_state(loan, WorkflowState.CONSENSUS)
        _audit(db, loan.id, "STATE_TRANSITION", {"to": "CONSENSUS"})

        # 4. Final score calculation
        #    Without moderator: 0.4*sales - 0.4*risk
        #    With moderator:    0.3*sales - 0.3*risk + 0.2*(moderator - 50)
        #    Moderator score is centred at 50 so a neutral moderator adds 0.
        if moderator_result is not None:
            final_score = (
                0.3 * sales_result.score
                - 0.3 * risk_result.score
                + 0.2 * (moderator_result.score - 50)
            )
            formula = "0.3*sales - 0.3*risk + 0.2*(mod-50)"
        else:
            final_score = 0.4 * sales_result.score - 0.4 * risk_result.score
            formula = "0.4*sales - 0.4*risk"

        loan.final_score = round(final_score, 2)
        _audit(db, loan.id, "FINAL_SCORE_CALC", {
            "formula": formula,
            "sales": sales_result.score,
            "risk": risk_result.score,
            "moderator": moderator_result.score if moderator_result else None,
            "final_score": loan.final_score,
        })

        # 5. Decision: >20 = Approved, else = Rejected
        loan.status = "Approved" if loan.final_score > 20 else "Rejected"
        _audit(db, loan.id, "DECISION", {"threshold": 20, "status": loan.status})

        # 6. confidence_score from sales-risk variance (consensus strength)
        variance = abs(sales_result.score - risk_result.score)
        loan.confidence_score = _confidence_from_variance(sales_result.score, risk_result.score)
        _audit(db, loan.id, "CONFIDENCE_CALC", {
            "sales_score": sales_result.score,
            "risk_score": risk_result.score,
            "variance": variance,
            "confidence": loan.confidence_score,
        })

        # --- FINALIZED ---
        _set_state(loan, WorkflowState.FINALIZED)
        _audit(db, loan.id, "STATE_TRANSITION", {"to": "FINALIZED"})
        _audit(db, loan.id, "WORKFLOW_COMPLETE", {"status": loan.status, "final_score": loan.final_score})

    db.commit()
    return loan
