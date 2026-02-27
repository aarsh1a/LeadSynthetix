"""LLM-based extraction fallback when regex misses fields."""

from app.extraction.schemas import ExtractionResult
from app.services.llm_service import LLMService


def extract_with_llm(text: str, llm: LLMService) -> ExtractionResult | None:
    """Use LLM to extract when API key is available."""
    prompt = f"""Extract the following from this financial document. Return ONLY valid JSON, no markdown.

Text:
{text[:12000]}

Return this exact JSON structure (use null for missing numeric fields, false for collateral_present if not mentioned, empty list for compliance_keywords if none):
{{
  "revenue": <number or null>,
  "debt": <number or null>,
  "dscr": <number or null>,
  "collateral_present": <true/false>,
  "compliance_keywords": ["keyword1", "keyword2"]
}}

Search for: offshore, grey list, gray list, AML, anti-money laundering, sanctions, PEP, politically exposed.
Numbers should be in base units (e.g. 12.5 for $12.5M).
"""
    response = llm.complete(prompt)
    if not response:
        return None
    try:
        import json
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        data = json.loads(cleaned)
        return ExtractionResult(
            revenue=data.get("revenue"),
            debt=data.get("debt"),
            dscr=data.get("dscr"),
            collateral_present=bool(data.get("collateral_present", False)),
            compliance_keywords=list(data.get("compliance_keywords", [])),
        )
    except Exception:
        return None
