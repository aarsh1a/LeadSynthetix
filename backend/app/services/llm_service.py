"""LLM service abstraction - OpenAI integration."""

import json
from typing import Any

from openai import OpenAI

from app.config import get_settings


class LLMService:
    """Abstracts OpenAI API for extraction and other LLM use cases."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client: OpenAI | None = (
            OpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )

    def complete(self, prompt: str, max_tokens: int = 1000) -> str | None:
        """Run completion and return content or None if unavailable."""
        if not self._client:
            return None
        try:
            resp = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0,
            )
            if resp.choices:
                return resp.choices[0].message.content
        except Exception:
            pass
        return None

    def complete_json(self, prompt: str, max_tokens: int = 1000) -> dict[str, Any] | None:
        """Run completion with JSON response format. Returns parsed dict or None."""
        if not self._client:
            return None
        try:
            resp = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0,
                response_format={"type": "json_object"},
            )
            if resp.choices and resp.choices[0].message.content:
                return json.loads(resp.choices[0].message.content)
        except Exception:
            pass
        return None
