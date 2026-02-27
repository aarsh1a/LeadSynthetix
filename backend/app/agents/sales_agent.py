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

    DEBATE_PROMPT = """You are a sales agent in a multi-agent debate about a loan application.
You have seen the other agents' arguments below. Respond to their points, defend your
position where you have evidence, and update your score if their arguments are compelling.
Be specific about which agent's points you agree or disagree with.
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
            memo="Sales review unavailable.",
            score=50.0,
            flags=[],
        )
