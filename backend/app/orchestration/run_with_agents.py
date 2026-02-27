"""
Run workflow with explicit agent results (for deterministic testing).
"""

import math
from typing import Any

from app.models.loan_application import LoanApplication
from app.orchestration.states import WorkflowState
from app.agents.schemas import AgentResult


def _confidence_from_variance(scores: list[float]) -> float:
    if len(scores) < 2:
        return 1.0
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std = math.sqrt(variance)
    return round(max(0.2, 1.0 - (std / 50)), 2)


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

    if loan.compliance_flag:
        loan.status = "Rejected"
        loan.final_score = 0.0
        loan.confidence_score = 1.0
        output["final_score"] = 0.0
        output["final_decision"] = "Rejected"
        output["confidence_score"] = 1.0
        output["auto_rejected"] = True
        return loan, output

    diff = abs(sales_result.score - risk_result.score)
    output["moderator_triggered"] = diff > 20

    if moderator_result and diff > 20:
        output["moderator_score"] = moderator_result.score

    sales_for_final = sales_result.score
    risk_for_final = risk_result.score
    final_score = 0.4 * sales_for_final - 0.4 * risk_for_final
    loan.final_score = round(final_score, 2)
    loan.status = "Approved" if loan.final_score > 20 else "Rejected"

    scores = [sales_result.score, risk_result.score, compliance_result.score]
    if moderator_result and diff > 20:
        scores.append(moderator_result.score)
    loan.confidence_score = _confidence_from_variance(scores)

    output["final_score"] = loan.final_score
    output["final_decision"] = loan.status
    output["confidence_score"] = loan.confidence_score

    return loan, output
