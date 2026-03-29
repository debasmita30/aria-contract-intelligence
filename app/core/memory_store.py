"""
ARIA — Semantic Memory Store
Pattern-frequency memory with recovery strategy effectiveness tracking.
Persists to JSON for cross-session learning.
"""

from __future__ import annotations
import json
import os
import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger("aria.memory")

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "memory.json")


class SemanticMemoryStore:
    """
    In-memory + JSON-persisted store for:
      - Clause patterns (pattern → fix, frequency)
      - Recovery effectiveness (failure_type → strategy → success_rate)
      - Reliability trend
    """

    def __init__(self, persist: bool = True):
        self.persist  = persist
        self.patterns: dict[str, dict] = {}
        self.recovery_stats: dict[str, dict] = defaultdict(lambda: defaultdict(int))
        self.reliability_trend: list[float]  = []
        self._load()

    # ── Pattern memory ─────────────────────────────────────────
    def store_pattern(self, pattern: str, fix: str, context: str = "") -> None:
        key = pattern.lower().strip()
        if key in self.patterns:
            self.patterns[key]["seen"] += 1
        else:
            self.patterns[key] = {"pattern": pattern, "fix": fix, "seen": 1, "context": context}
        self._save()

    def get_top_patterns(self, n: int = 5) -> list[dict]:
        sorted_p = sorted(self.patterns.values(), key=lambda x: x["seen"], reverse=True)
        return sorted_p[:n]

    # ── Recovery memory ────────────────────────────────────────
    def store_recovery(self, failure_type: str, strategy: str, pre_reliability: float) -> None:
        self.recovery_stats[failure_type][strategy] += 1
        self._save()

    def best_recovery_strategy(self, failure_type: str) -> str | None:
        stats = self.recovery_stats.get(failure_type)
        if not stats:
            return None
        return max(stats, key=lambda s: stats[s])

    # ── Reliability trend ──────────────────────────────────────
    def store_reliability_datapoint(self, reliability: float) -> None:
        self.reliability_trend.append(round(reliability, 4))
        if len(self.reliability_trend) > 100:
            self.reliability_trend = self.reliability_trend[-100:]
        self._save()

    def mean_reliability(self) -> float:
        if not self.reliability_trend:
            return 0.0
        return sum(self.reliability_trend) / len(self.reliability_trend)

    # ── Persistence ────────────────────────────────────────────
    def _save(self) -> None:
        if not self.persist:
            return
        try:
            os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
            with open(MEMORY_PATH, "w") as f:
                json.dump({
                    "patterns":          self.patterns,
                    "recovery_stats":    dict(self.recovery_stats),
                    "reliability_trend": self.reliability_trend,
                }, f, indent=2)
        except Exception as exc:
            logger.warning("Memory save failed: %s", exc)

    def _load(self) -> None:
        try:
            if os.path.exists(MEMORY_PATH):
                with open(MEMORY_PATH) as f:
                    data = json.load(f)
                self.patterns          = data.get("patterns", {})
                self.recovery_stats    = defaultdict(
                    lambda: defaultdict(int),
                    {k: defaultdict(int, v) for k, v in data.get("recovery_stats", {}).items()}
                )
                self.reliability_trend = data.get("reliability_trend", [])
        except Exception as exc:
            logger.warning("Memory load failed: %s", exc)
