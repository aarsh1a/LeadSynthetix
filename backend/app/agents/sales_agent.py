"""Sales Agent - optimistic, growth-oriented."""

import json
from typing import Any

from app.agents.schemas import AgentResult
from app.services.llm_service import LLMService


class SalesAgent:
    """Optimistic, growth-oriented. Highlights strengths, justifies approval."""

    SYSTEM_PROMPT = """You are a sales agent evaluating loan applications.
You are optimistic and growth-oriented. Highlight strengths, justify approval.
Return ONLY valid JSON in this exact structure:
{"memo": "<your memo text>", "score": <0-100>, "flags": ["<flag1>", "<flag2>"]}
Score: higher for strong revenue, collateral, growth potential.
Flags: optional list of positive or cautionary notes."""

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
            memo="Sales review unavailable.",
            score=50.0,
            flags=[],
        )
