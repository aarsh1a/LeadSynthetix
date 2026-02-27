"""Risk Matrix service - generates category scores with evidence."""

from typing import Any

from app.scoring.risk_matrix import compute_risk_matrix
from app.scoring.schemas import RiskMatrixResult


def get_risk_matrix(financials: dict[str, Any]) -> RiskMatrixResult:
    """
    Generate Risk Matrix from structured financials. Fully deterministic.
    No LLM calls.
    """
    return compute_risk_matrix(financials)
