"""
ARIA — Risk Agent
Computes multi-dimensional risk scores per domain.
"""

from __future__ import annotations
import re
import logging
from typing import Any

logger = logging.getLogger("aria.risk")

RISK_DIMENSIONS = {
    "Liability":     [r"liability", r"indemnif", r"damages", r"negligence"],
    "Termination":   [r"terminat", r"exit\s+fee", r"early\s+exit"],
    "Payment":       [r"payment", r"invoice", r"late\s+fee", r"interest"],
    "Compliance":    [r"gdpr", r"sox", r"hipaa", r"ccpa", r"regulatory"],
    "Data Privacy":  [r"personal\s+data", r"data\s+breach", r"data\s+transfer", r"encryption"],
    "IP":            [r"intellectual\s+property", r"proprietary", r"license"],
    "Jurisdiction":  [r"governing\s+law", r"jurisdiction", r"arbitration"],
}

HIGH_RISK_AMPLIFIERS = [
    r"unlimited", r"sole\s+discretion", r"all\s+claims", r"any\s+and\s+all",
    r"no\s+limit", r"gross\s+negligence", r"willful\s+misconduct",
]


class RiskAgent:
    def __init__(self, llm: Any):
        self.llm = llm

    def run(self, state: Any, simulate_failure: bool = False) -> dict:
        text  = state.contract_text.lower()
        scores = {}

        for dim, patterns in RISK_DIMENSIONS.items():
            # Base score: how many risk keywords appear?
            hits = sum(1 for p in patterns if re.search(p, text))
            base = min(0.9, hits * 0.18)

         
            amplified = any(re.search(amp, text) for amp in HIGH_RISK_AMPLIFIERS)
            if amplified:
                base = min(0.95, base + 0.20)

            scores[dim] = round(max(0.1, base), 2)

        if simulate_failure:
            scores["Compliance"] = min(0.95, scores.get("Compliance", 0.3) + 0.35)
            scores["Liability"]  = min(0.95, scores.get("Liability",  0.4) + 0.20)

       
        confidence = round(1.0 - (sum(scores.values()) / len(scores)), 3)
        confidence = max(0.30, min(0.95, confidence))

        return {
            "risk_scores": scores,
            "confidence":  confidence,
            "high_risk_domains": [k for k, v in scores.items() if v > 0.65],
        }
