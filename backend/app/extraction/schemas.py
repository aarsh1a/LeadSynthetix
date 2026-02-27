"""Extraction schemas - structured output."""

from pydantic import BaseModel


class ExtractionResult(BaseModel):
    """Structured extraction result returned by the API."""

    revenue: float | None = None
    debt: float | None = None
    dscr: float | None = None
    collateral_present: bool = False
    compliance_keywords: list[str] = []
