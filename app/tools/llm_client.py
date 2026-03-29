"""
ARIA — LLM Client
Unified client supporting:
  - Anthropic Claude (claude-sonnet-4-20250514)
  - OpenAI GPT-4o
  - No-key demo mode (returns structured fallback responses)
"""

from __future__ import annotations
import os
import logging
from typing import Any

logger = logging.getLogger("aria.llm")

DEFAULT_SYSTEM = (
    "You are ARIA, an enterprise contract intelligence system. "
    "You are precise, concise, and legally astute. "
    "Always structure your responses to be actionable."
)


class LLMClient:
    """
    Thin wrapper around Anthropic / OpenAI APIs.
    Falls back to a deterministic stub when no key is provided.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key  = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.provider = self._detect_provider()
        self._client  = self._init_client()

    # ── Public API ─────────────────────────────────────────────
    def complete(
        self,
        prompt:      str,
        system:      str       = DEFAULT_SYSTEM,
        max_tokens:  int       = 500,
        temperature: float     = 0.2,
    ) -> str:
        """Send a completion request. Returns the text response."""
        if self._client is None:
            return self._stub_response(prompt)

        try:
            if self.provider == "anthropic":
                return self._anthropic_complete(prompt, system, max_tokens, temperature)
            if self.provider == "openai":
                return self._openai_complete(prompt, system, max_tokens, temperature)
        except Exception as exc:
            logger.warning("LLM API error (%s): %s — using stub", self.provider, exc)

        return self._stub_response(prompt)

    # ── Provider detection ─────────────────────────────────────
    def _detect_provider(self) -> str | None:
        if not self.api_key:
            return None
        if self.api_key.startswith("sk-ant"):
            return "anthropic"
        if self.api_key.startswith("sk-"):
            return "openai"
        return None

    def _init_client(self) -> Any:
        if self.provider == "anthropic":
            try:
                import anthropic
                return anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("anthropic package not installed — pip install anthropic")
        elif self.provider == "openai":
            try:
                import openai
                return openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("openai package not installed — pip install openai")
        return None

    # ── Provider implementations ───────────────────────────────
    def _anthropic_complete(
        self, prompt: str, system: str, max_tokens: int, temperature: float
    ) -> str:
        msg = self._client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    def _openai_complete(
        self, prompt: str, system: str, max_tokens: int, temperature: float
    ) -> str:
        resp = self._client.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
        )
        return resp.choices[0].message.content

    # ── Demo stub ──────────────────────────────────────────────
    def _stub_response(self, prompt: str) -> str:
        """Returns a plausible response without hitting any API."""
        prompt_lower = prompt.lower()
        if "recovery" in prompt_lower or "strategy" in prompt_lower:
            return "simplify_reparse"
        if "summarise" in prompt_lower or "summary" in prompt_lower:
            return (
                "**Analysis complete.** Key risks identified in liability cap and indemnification "
                "clauses. GDPR Article 28 referenced but DPA execution not confirmed. "
                "Recommend prioritising §3 (Liability) and §4 (Indemnification) for immediate review."
            )
        if "extract" in prompt_lower or "clause" in prompt_lower:
            return "[]"  # triggers regex fallback
        return "Analysis complete. No API key provided — running in demo mode."
