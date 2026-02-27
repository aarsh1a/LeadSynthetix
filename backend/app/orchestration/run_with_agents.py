"""
Run workflow with explicit agent results (for deterministic testing).
"""

from typing import Any

from app.models.loan_application import LoanApplication
from app.orchestration.states import WorkflowState
from app.agents.schemas import AgentResult


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
        confidence = 1.0 - 0.01 * variance
    elif variance <= 20:
        confidence = 0.9 - 0.02 * (variance - 10)
    elif variance <= 40:
        confidence = 0.7 - 0.01 * (variance - 20)
    else:
        confidence = max(0.1, 0.5 - 0.005 * (variance - 40))

    return round(confidence, 2)


def run_workflow_with_results(
    loan: LoanApplication,
    sales_result: AgentResult,
    risk_result: AgentResult,
    compliance_result: AgentResult,
    moderator_result: AgentResult | None = None,
) -> tuple[LoanApplication, dict[str, Any]]:
    """
    Run decision logic with pre-computed agent results. No DB, no LLM.
    Returns (updated loan, output dict with agent scores, final score, etc.)
    """
    output: dict[str, Any] = {
        "agent_scores": {
            "Sales": sales_result.score,
            "Risk": risk_result.score,
            "Compliance": compliance_result.score,
        },
        "moderator_triggered": False,
        "moderator_score": None,
        "compliance_flag": loan.compliance_flag,
        "final_score": None,
        "final_decision": None,
        "confidence_score": None,
        "auto_rejected": False,
    }

    # Compliance veto: keyword flag OR agent score < 30 OR agent flagged keywords
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
        loan.status = "Rejected"
        loan.final_score = 0.0
        loan.confidence_score = 1.0
        loan.compliance_flag = True
        loan.workflow_state = WorkflowState.FINALIZED.value
        output["final_score"] = 0.0
        output["final_decision"] = "Rejected"
        output["confidence_score"] = 1.0
        output["auto_rejected"] = True
        return loan, output

    diff = abs(sales_result.score - risk_result.score)
    output["moderator_triggered"] = diff > 20

    if moderator_result and diff > 20:
        output["moderator_score"] = moderator_result.score

    # Final score: blend moderator when triggered
    if moderator_result and diff > 20:
        final_score = (
            0.3 * sales_result.score
            - 0.3 * risk_result.score
            + 0.2 * (moderator_result.score - 50)
        )
    else:
        final_score = 0.4 * sales_result.score - 0.4 * risk_result.score
    loan.final_score = round(final_score, 2)
    loan.status = "Approved" if loan.final_score > 20 else "Rejected"

    loan.confidence_score = _confidence_from_variance(sales_result.score, risk_result.score)

    loan.workflow_state = WorkflowState.FINALIZED.value

    output["final_score"] = loan.final_score
    output["final_decision"] = loan.status
    output["confidence_score"] = loan.confidence_score

    return loan, output
