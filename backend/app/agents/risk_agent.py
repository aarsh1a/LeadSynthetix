"""Risk Agent - skeptical, data-driven."""

import json
from typing import Any

from app.agents.schemas import AgentResult
from app.services.llm_service import LLMService


class RiskAgent:
    """Skeptical, data-driven. Focuses on DSCR, leverage, volatility."""

    SYSTEM_PROMPT = """You are a risk agent evaluating loan applications.
You are skeptical and data-driven. Focus on DSCR, leverage, volatility.
Return ONLY valid JSON in this exact structure:
{"memo": "<your memo text>", "score": <0-100>, "flags": ["<flag1>", "<flag2>"]}
Score: higher for strong DSCR (>1.25), low leverage, stable cash flow. Lower for weak DSCR, high debt.
Flags: list risk concerns (e.g. low DSCR, high leverage)."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm

    def evaluate(self, financials: dict[str, Any]) -> AgentResult:
        """Generate memo, score, flags from structured financial JSON."""
        prompt = f"""{self.SYSTEM_PROMPT}

Financial data:
{json.dumps(financials, indent=2)}

Return JSON only."""

        raw = self._llm.complete_json(prompt, max_tokens=800)
        if raw:
            s = max(0, min(100, float(raw.get("score", 50))))
            return AgentResult(
                memo=str(raw.get("memo", "")),
                score=s,
                flags=list(raw.get("flags", [])),
            )
        return AgentResult(
            memo="Risk review unavailable.",
            score=50.0,
            flags=[],
        )
