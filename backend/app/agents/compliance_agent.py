"""Compliance Agent - procedural, blocks AML and offshore risks."""

import json
from typing import Any

from app.agents.schemas import AgentResult
from app.services.llm_service import LLMService


class ComplianceAgent:
    """Procedural, blocks AML, grey list, offshore risks."""

    SYSTEM_PROMPT = """You are a compliance agent evaluating loan applications.
You are procedural and strict. Block AML, grey list, offshore risks.
Return ONLY valid JSON in this exact structure:
{"memo": "<your memo text>", "score": <0-100>, "flags": ["<flag1>", "<flag2>"]}
Score: 0-30 if compliance_keywords include offshore/AML/grey list; 70-100 if clean.
Flags: list compliance issues (e.g. offshore mention, AML concern, grey list)."""

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
            memo="Compliance review unavailable.",
            score=50.0,
            flags=[],
        )
