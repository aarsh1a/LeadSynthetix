"""Risk Matrix output schemas - structured JSON for UI visualization."""

from pydantic import BaseModel, Field


class CategoryScore(BaseModel):
    """Single category score with linked evidence."""

    score: int = Field(ge=1, le=10, description="Score 1-10")
    evidence: list[str] = Field(default_factory=list, description="Linked evidence")


class RiskMatrixResult(BaseModel):
    """Structured risk matrix for UI visualization."""

    financial_risk: CategoryScore = Field(description="Financial Risk 1-10, 10=highest")
    growth_strength: CategoryScore = Field(description="Growth Strength 1-10, 10=strongest")
    regulatory_risk: CategoryScore = Field(description="Regulatory Risk 1-10, 10=highest")
    reputation_risk: CategoryScore = Field(description="Reputation Risk 1-10, 10=highest")
