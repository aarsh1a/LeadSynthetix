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

    DEBATE_PROMPT = """You are a compliance agent in a multi-agent debate about a loan application.
You have seen the other agents' arguments below. Reassess compliance risk in light of
their observations. If other agents identified facts that change the risk picture,
adjust your score. Be firm on regulatory red-lines but fair on borderline cases.
Return ONLY valid JSON in this exact structure:
{"memo": "<your rebuttal/updated memo>", "score": <0-100>, "flags": ["<flag1>"]}"""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm

    def evaluate(
        self,
        financials: dict[str, Any],
        prior_memos: list[dict[str, Any]] | None = None,
    ) -> AgentResult:
        """Generate memo, score, flags. If prior_memos provided, this is a debate round."""
        if prior_memos:
            memos_text = "\n".join(
                f"[{m['agent']}] (score {m['score']}): {m['memo']}"
                for m in prior_memos
            )
            prompt = f"""{self.DEBATE_PROMPT}

Financial data:
{json.dumps(financials, indent=2)}

Prior agent memos:
{memos_text}

Return JSON only."""
        else:
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
