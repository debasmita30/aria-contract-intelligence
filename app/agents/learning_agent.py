"""
ARIA — Learning Agent
Updates semantic memory with patterns from each workflow run.
Enables ARIA to improve over time without retraining.
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger("aria.learning")


class LearningAgent:
    """
    Observes each workflow run and extracts re-usable patterns into memory.

    What it learns:
      - Common failure patterns and which recovery strategy worked
      - Recurring high-risk clause structures
      - Compliance gaps that appear repeatedly
    """

    def __init__(self, memory: Any):
        self.memory = memory

    def update(self, state: Any) -> None:
        # 1. Learn from high-risk clauses
        extraction = state.agent_results.get("Extraction", {})
        for clause in extraction.get("clauses", []):
            if clause.get("risk") == "HIGH":
                self.memory.store_pattern(
                    pattern=clause["clause"],
                    fix=clause.get("suggestion", "Review with legal counsel."),
                    context="extraction",
                )

        # 2. Learn from compliance flags
        compliance = state.agent_results.get("Compliance", {})
        for flag in compliance.get("flags", []):
            self.memory.store_pattern(
                pattern=f'{flag["framework"]}: {flag["description"]}',
                fix=flag.get("remediation", "Address compliance gap."),
                context="compliance",
            )

        # 3. Store reliability trend
        if hasattr(state, "reliability") and state.reliability:
            self.memory.store_reliability_datapoint(state.reliability)

        logger.info("Learning agent updated memory with %d patterns",
                    len(extraction.get("clauses", [])) + len(compliance.get("flags", [])))
