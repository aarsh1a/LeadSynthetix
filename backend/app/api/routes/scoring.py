"""Scoring API routes."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.risk_matrix_service import get_risk_matrix
from app.scoring.schemas import RiskMatrixResult

router = APIRouter(prefix="/scoring", tags=["scoring"])


class RiskMatrixRequest(BaseModel):
    """Request body for risk matrix computation."""

    revenue: float | None = None
    debt: float | None = None
    dscr: float | None = None
    collateral_present: bool = False
    compliance_keywords: list[str] = []


@router.post("/risk-matrix", response_model=RiskMatrixResult)
def compute_risk_matrix_api(request: RiskMatrixRequest) -> RiskMatrixResult:
    """Compute Risk Matrix from financials. Fully deterministic, no LLM."""
    financials = request.model_dump()
    return get_risk_matrix(financials)
