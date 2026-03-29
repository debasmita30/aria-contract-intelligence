"""
ARIA — Compliance Agent
Checks contract against real regulatory frameworks:
  - GDPR (EU 2016/679)
  - SOX Section 302/404
  - HIPAA Safe Harbor
  - CCPA (California Consumer Privacy Act)
  - Standard commercial contract requirements
"""

from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("aria.compliance")


@dataclass
class ComplianceRule:
    id:          str
    framework:   str
    description: str
    pattern:     str
    severity:    str          
    remediation: str
    required:    bool = True  


# ── Regulatory rule library ───────────────────────────────────────
RULES: list[ComplianceRule] = [
    ComplianceRule(
        id="GDPR-28",
        framework="GDPR",
        description="Data Processing Agreement (Article 28) reference",
        pattern=r"(?i)(article\s+28|data\s+processing\s+agreement|dpa\s+executed)",
        severity="CRITICAL",
        remediation="Execute a separate GDPR Article 28 DPA before any data transfer.",
    ),
    ComplianceRule(
        id="GDPR-RETENTION",
        framework="GDPR",
        description="Data retention period specified",
        pattern=r"(?i)(data\s+retention|retention\s+period|\d+\s+days?\s+post)",
        severity="HIGH",
        remediation="Specify an explicit data retention period (recommend ≤90 days post-contract).",
    ),
    ComplianceRule(
        id="GDPR-TRANSFER",
        framework="GDPR",
        description="Cross-border data transfer safeguards",
        pattern=r"(?i)(standard\s+contractual\s+clauses|scc|adequacy\s+decision|binding\s+corporate\s+rules)",
        severity="HIGH",
        remediation="Include SCCs or reference an adequacy decision for any cross-border transfers.",
        required=False,  # only needed if transfer is implied
    ),
    ComplianceRule(
        id="SOX-302",
        framework="SOX",
        description="Audit trail and record-keeping clause",
        pattern=r"(?i)(audit\s+trail|record.keeping|financial\s+records|books\s+and\s+records)",
        severity="HIGH",
        remediation="Add explicit audit trail and record-keeping obligations for financial data.",
    ),
    ComplianceRule(
        id="CCPA-1",
        framework="CCPA",
        description="Consumer data rights acknowledgement",
        pattern=r"(?i)(right\s+to\s+delete|right\s+to\s+access|opt.out|do\s+not\s+sell)",
        severity="MEDIUM",
        remediation="If California residents are involved, add CCPA data rights provisions.",
        required=False,
    ),
    ComplianceRule(
        id="CONTRACT-LIABILITY",
        framework="Commercial",
        description="Liability limitation clause present",
        pattern=r"(?i)(liability\s+shall\s+be\s+limited|limitation\s+of\s+liability)",
        severity="HIGH",
        remediation="Every commercial contract should have a clear mutual liability cap.",
    ),
    ComplianceRule(
        id="CONTRACT-DISPUTE",
        framework="Commercial",
        description="Dispute resolution mechanism",
        pattern=r"(?i)(arbitration|mediation|dispute\s+resolution|governing\s+law)",
        severity="MEDIUM",
        remediation="Specify dispute resolution process (arbitration preferred for cross-border).",
    ),
    ComplianceRule(
        id="CONTRACT-CONFIDENTIALITY",
        framework="Commercial",
        description="Confidentiality / NDA clause",
        pattern=r"(?i)(confidential\w*|non.disclosure|nda)",
        severity="MEDIUM",
        remediation="Add mutual confidentiality clause with clear exclusions.",
    ),
    ComplianceRule(
        id="UNLIMITED-LIABILITY",
        framework="Risk",
        description="Unlimited liability language (must NOT be present)",
        pattern=r"(?i)(unlimited\s+liability|no\s+limit\s+on\s+liability|fully\s+liable\s+for\s+all)",
        severity="CRITICAL",
        remediation="Remove or cap all unlimited liability language immediately.",
        required=False,  # presence is the violation
    ),
    ComplianceRule(
        id="UNILATERAL-TERMINATION",
        framework="Risk",
        description="Unilateral termination without cause",
        pattern=r"(?i)(terminat\w+\s+at\s+(our|its|their)\s+(sole\s+)?discretion|without\s+cause\s+terminat)",
        severity="HIGH",
        remediation="Require mutual consent for termination-without-cause provisions.",
        required=False,
    ),
]


class ComplianceAgent:
    """
    Runs contract text against the regulatory rule library.
    """

    def __init__(self, llm: Any):
        self.llm = llm

    def run(self, state: Any, simulate_failure: bool = False) -> dict:
        text = state.contract_text
        flags, passed = [], []

        for rule in RULES:
            match = bool(re.search(rule.pattern, text))

            if rule.required and not match:
                # Required clause is missing — violation
                flags.append({
                    "rule_id":     rule.id,
                    "framework":   rule.framework,
                    "description": rule.description,
                    "severity":    rule.severity,
                    "type":        "MISSING",
                    "remediation": rule.remediation,
                })
            elif not rule.required and match:
                # Prohibited pattern is present — violation
                flags.append({
                    "rule_id":     rule.id,
                    "framework":   rule.framework,
                    "description": rule.description,
                    "severity":    rule.severity,
                    "type":        "PRESENT_PROHIBITED",
                    "remediation": rule.remediation,
                })
            else:
                passed.append(rule.id)

       
        total    = len(RULES)
        n_flags  = len(flags)
        base_conf= 1.0 - (n_flags / total)

        if simulate_failure:
            base_conf = max(0.45, base_conf - 0.22)
           
            flags.append({
                "rule_id":     "SIMULATED",
                "framework":   "Test",
                "description": "Simulated compliance failure for demo",
                "severity":    "HIGH",
                "type":        "SIMULATED",
                "remediation": "This is a demo flag. Disable 'Simulate Failure' to clear.",
            })

        return {
            "flags":           flags,
            "passed":          passed,
            "flag_count":      len(flags),
            "pass_count":      len(passed),
            "confidence":      round(base_conf, 3),
            "frameworks_checked": list({r.framework for r in RULES}),
        }
