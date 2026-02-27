"""Agent output schemas - structured JSON responses."""

from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    """Structured output from an agent: memo, score, flags."""

    memo: str = Field(description="Agent memo text")
    score: float = Field(ge=0, le=100, description="Score from 0 to 100")
    flags: list[str] = Field(default_factory=list, description="Raised flags")
