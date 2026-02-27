"""Moderator Agent - weighs arguments, calculates final score, drives consensus."""

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

    CONSENSUS_PROMPT = """You are a moderator agent in a multi-round debate about a loan.
Below are the latest memos from all agents across debate rounds.
Your job is to:
1. Identify where agents agree and disagree.
2. Push agents toward consensus by highlighting strong arguments.
3. Provide your own risk-adjusted score.
4. In the "consensus" field, say true if agents are reasonably aligned (score spread < 15), false otherwise.

Return ONLY valid JSON:
{"memo": "<synthesis>", "score": <0-100>, "flags": ["<flag>"], "consensus": true/false}"""

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

    def evaluate_consensus(
        self,
        financials: dict[str, Any],
        all_memos: list[dict[str, Any]],
    ) -> tuple[AgentResult, bool]:
        """Evaluate debate memos and determine if consensus reached.

        Returns (AgentResult, consensus_reached: bool).
        """
        memos_text = "\n".join(
            f"[Round {m.get('round', '?')} - {m['agent']}] (score {m['score']}): {m['memo']}"
            for m in all_memos
        )
        prompt = f"""{self.CONSENSUS_PROMPT}

Financial data:
{json.dumps(financials, indent=2)}

All agent memos (chronological):
{memos_text}

Return JSON only."""

        raw = self._llm.complete_json(prompt, max_tokens=800)
        if raw:
            s = max(0, min(100, float(raw.get("score", 50))))
            consensus = bool(raw.get("consensus", False))
            return AgentResult(
                memo=str(raw.get("memo", "")),
                score=s,
                flags=list(raw.get("flags", [])),
            ), consensus
        return AgentResult(
            memo="Moderator consensus check unavailable.",
            score=50.0,
            flags=[],
        ), False
