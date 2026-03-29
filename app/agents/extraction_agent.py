"""
ARIA — Extraction Agent
Extracts key clauses from contract text using LLM + regex fallback.
"""

from __future__ import annotations
import re
import json
import logging
from typing import Any

logger = logging.getLogger("aria.extraction")

# ── Clause patterns for regex fallback ────────────────────────────
CLAUSE_PATTERNS = {
    "Liability Cap":     r"(?i)(liability\s+shall\s+be\s+limited|limitation\s+of\s+liability|cap\s+on\s+liability)",
    "GDPR Compliance":   r"(?i)(gdpr|general\s+data\s+protection|article\s+28|data\s+processing\s+agreement)",
    "Force Majeure":     r"(?i)(force\s+majeure|act\s+of\s+god|unforeseeable\s+event)",
    "Termination":       r"(?i)(terminat\w+\s+clause|right\s+to\s+terminat|terminat\w+\s+fee)",
    "Indemnification":   r"(?i)(indemnif\w+|hold\s+harmless|defend\s+and\s+indemnif)",
    "Governing Law":     r"(?i)(governed\s+by|governing\s+law|jurisdiction\s+of)",
    "Payment Terms":     r"(?i)(payment\s+terms?|invoice\s+due|net\s+\d+\s+days?|monthly\s+fee)",
    "Intellectual Property": r"(?i)(intellectual\s+property|ip\s+ownership|proprietary\s+rights)",
    "Confidentiality":   r"(?i)(confidential\w*|non-disclosure|nda)",
    "SLA / Uptime":      r"(?i)(service\s+level|sla|uptime\s+guarantee|\d+\.\d+%\s+availability)",
}

RISK_KEYWORDS = {
    "HIGH":   ["unlimited", "broad", "all claims", "any and all", "gross negligence",
               "intentional misconduct", "unlimited liability"],
    "MEDIUM": ["ambiguous", "subject to", "may not apply", "force majeure", "broadly",
               "material breach", "at our discretion"],
    "LOW":    ["limited to", "specified", "clearly defined", "mutual", "reasonable"],
}


class ExtractionAgent:
    """
    Extracts structured clause data from contract text.

    Pipeline:
      1. Attempt LLM-based extraction (structured JSON output)
      2. Fallback: regex-based clause detection
      3. Risk classification per clause
    """

    def __init__(self, llm: Any):
        self.llm = llm

    def run(self, state: Any, simulate_failure: bool = False) -> dict:
        text = state.contract_text

        # Attempt LLM extraction first
        clauses = self._llm_extract(text)
        if not clauses:
            # Regex fallback
            clauses = self._regex_extract(text)

        # If simulating failure, degrade one clause confidence
        if simulate_failure:
            for c in clauses:
                if c.get("risk") == "HIGH":
                    c["confidence"] = 0.52
                    c["status"] = "⚠ Low Confidence"

        overall_confidence = self._compute_confidence(clauses, simulate_failure)

        return {
            "clauses":    clauses,
            "confidence": overall_confidence,
            "clause_count": len(clauses),
        }

    # ── LLM extraction ─────────────────────────────────────────
    def _llm_extract(self, text: str) -> list[dict]:
        prompt = f"""Extract ALL key legal clauses from the following contract.

Return ONLY a valid JSON array. Each element must have:
- "clause": string (clause name)
- "status": string (e.g. "✓ Present", "⚠ Ambiguous", "✗ Missing", "⚠ Broad")
- "risk": one of "HIGH", "MEDIUM", "LOW"
- "suggestion": string (one actionable recommendation)
- "confidence": float 0-1

Contract text:
\"\"\"
{text[:3000]}
\"\"\"

Return ONLY the JSON array, no other text."""

        try:
            raw = self.llm.complete(prompt, max_tokens=800)
            # Strip markdown fences if present
            raw = re.sub(r"```(?:json)?|```", "", raw).strip()
            clauses = json.loads(raw)
            if isinstance(clauses, list) and clauses:
                return clauses
        except Exception as exc:
            logger.warning("LLM extraction failed: %s — using regex fallback", exc)
        return []

    # ── Regex fallback ─────────────────────────────────────────
    def _regex_extract(self, text: str) -> list[dict]:
        clauses = []
        for clause_name, pattern in CLAUSE_PATTERNS.items():
            matches = re.findall(pattern, text)
            if not matches:
                continue

            # Find surrounding sentence for risk classification
            sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if s.strip()]
            relevant  = [s for s in sentences if re.search(pattern, s)]
            context   = " ".join(relevant[:2])

            risk       = self._classify_risk(context)
            status     = self._infer_status(clause_name, context, risk)
            suggestion = self._generate_suggestion(clause_name, risk, context)
            confidence = 0.85 if risk == "LOW" else 0.72 if risk == "MEDIUM" else 0.62

            clauses.append({
                "clause":     clause_name,
                "status":     status,
                "risk":       risk,
                "suggestion": suggestion,
                "confidence": confidence,
                "context":    context[:150],
            })

        if not clauses:
            clauses.append({
                "clause":     "Unstructured Contract",
                "status":     "⚠ Unable to parse",
                "risk":       "HIGH",
                "suggestion": "Reformat document with standard clause headings.",
                "confidence": 0.40,
            })
        return clauses

    # ── Helpers ─────────────────────────────────────────────────
    def _classify_risk(self, context: str) -> str:
        text_lower = context.lower()
        for level in ("HIGH", "MEDIUM", "LOW"):
            if any(kw in text_lower for kw in RISK_KEYWORDS[level]):
                return level
        return "MEDIUM"

    def _infer_status(self, clause: str, context: str, risk: str) -> str:
        if risk == "HIGH":
            return "⚠ Ambiguous / High Risk"
        if risk == "MEDIUM":
            return "⚠ Review Required"
        return "✓ Present"

    def _generate_suggestion(self, clause: str, risk: str, context: str) -> str:
        suggestions = {
            "Liability Cap":     "Specify an explicit monetary cap tied to contract value.",
            "GDPR Compliance":   "Ensure a signed DPA exists before data processing begins.",
            "Force Majeure":     "Expand to include cyber events, pandemics, and supply-chain disruption.",
            "Termination":       "Clarify notice periods and add fee schedule as an exhibit.",
            "Indemnification":   "Narrow scope to direct damages only; remove 'any and all claims'.",
            "Governing Law":     "Confirm jurisdiction aligns with GDPR enforcement territory.",
            "Payment Terms":     "Add late payment interest rate and dispute resolution timeline.",
            "Intellectual Property": "Clarify work-for-hire vs. licensed IP; specify ownership on day 1.",
            "Confidentiality":   "Define 'confidential information' explicitly; set post-term duration.",
            "SLA / Uptime":      "Specify measurement methodology and credit calculation formula.",
        }
        base = suggestions.get(clause, "Review clause with legal counsel.")
        if risk == "HIGH":
            return f"⚡ Priority: {base}"
        return base

    def _compute_confidence(self, clauses: list[dict], simulate_failure: bool) -> float:
        if not clauses:
            return 0.30
        scores = [c.get("confidence", 0.75) for c in clauses]
        mean   = sum(scores) / len(scores)
        if simulate_failure:
            return max(0.45, mean - 0.18)
        return round(mean, 3)
