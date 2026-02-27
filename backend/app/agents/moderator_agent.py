"""Moderator Agent - weighs arguments, calculates final score."""

import json
from typing import Any

from app.agents.schemas import AgentResult
from app.services.llm_service import LLMService


class ModeratorAgent:
    """Weighs arguments from other agents, calculates final risk-adjusted score."""

    SYSTEM_PROMPT = """You are a moderator agent synthesizing agent outputs.
Weigh Sales, Risk, and Compliance arguments. Calculate a final risk-adjusted score.
Return ONLY valid JSON in this exact structure:
{"memo": "<your synthesis memo>", "score": <0-100>, "flags": ["<flag1>", "<flag2>"]}
Score: risk-adjusted blend of agent scores; weight Risk and Compliance higher for safety.
Flags: critical issues that affect final decision."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm

    def evaluate(
        self,
        financials: dict[str, Any],
        agent_outputs: dict[str, dict[str, Any]],
    ) -> AgentResult:
        """Generate memo, score, flags from financials and prior agent outputs."""
        prompt = f"""{self.SYSTEM_PROMPT}

Financial data:
{json.dumps(financials, indent=2)}

Agent outputs (Sales, Risk, Compliance):
{json.dumps(agent_outputs, indent=2)}

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
            memo="Moderator synthesis unavailable.",
            score=50.0,
            flags=[],
        )
