"""Orchestrates extraction: regex first, LLM fallback for missing fields."""

from app.extraction.schemas import ExtractionResult
from app.extraction.regex_extractor import extract_with_regex
from app.extraction.llm_extractor import extract_with_llm
from app.services.llm_service import LLMService


def extract(text: str, llm: LLMService | None = None) -> ExtractionResult:
    """Extract using regex, then LLM fallback for missing fields."""
    result = extract_with_regex(text)

    # LLM fallback if fields missing and LLM available
    if llm is None:
        llm = LLMService()
    needs_fallback = (
        result.revenue is None
        or result.debt is None
        or result.dscr is None
    )
    if needs_fallback and llm:
        llm_result = extract_with_llm(text, llm)
        if llm_result:
            if result.revenue is None and llm_result.revenue is not None:
                result.revenue = llm_result.revenue
            if result.debt is None and llm_result.debt is not None:
                result.debt = llm_result.debt
            if result.dscr is None and llm_result.dscr is not None:
                result.dscr = llm_result.dscr
            if not result.collateral_present and llm_result.collateral_present:
                result.collateral_present = llm_result.collateral_present
            if not result.compliance_keywords and llm_result.compliance_keywords:
                result.compliance_keywords = llm_result.compliance_keywords

    return result
