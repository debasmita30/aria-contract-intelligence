"""
ARIA — CLI Demo Runner
Run the full ARIA pipeline from the command line.

Usage:
    # Demo mode (no API key needed)
    python demo/run_demo.py

    # With real LLM reasoning
    ANTHROPIC_API_KEY=sk-ant-... python demo/run_demo.py

    # Simulate a failure + recovery
    python demo/run_demo.py --failure

    # Use a custom contract file
    python demo/run_demo.py --contract path/to/contract.txt
"""

from __future__ import annotations
import sys
import os
import json
import argparse
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Colour helpers (works on any terminal) ────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"
MAGENTA= "\033[95m"

def h(text: str, colour: str = CYAN) -> str:
    return f"{colour}{text}{RESET}"

def header(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*60}{RESET}")

def kv(key: str, val: str, colour: str = CYAN) -> None:
    print(f"  {DIM}{key:<30}{RESET}{colour}{val}{RESET}")

# ── Sample contract ───────────────────────────────────────────────
SAMPLE_CONTRACT = """SERVICE AGREEMENT

This Agreement is entered into as of January 1, 2025 between Acme Corp ("Client")
and TechServ Inc ("Provider").

1. SERVICES
Provider shall deliver cloud infrastructure management services including uptime
guarantees of 99.5%, subject to force majeure events.

2. PAYMENT TERMS
Client agrees to pay $50,000 per month. Payments are due within 30 days of invoice.
Late payments shall incur a 1.5% monthly interest charge.

3. LIABILITY
Provider's liability shall be limited to three months of service fees. However,
in cases of gross negligence or intentional misconduct, this limitation may not apply.
The indemnification clause applies broadly to all third-party claims arising from
Provider's performance.

4. TERMINATION
Either party may terminate with 60 days written notice. Provider may terminate
immediately upon material breach. Termination fees apply if Client exits within
the first 12 months.

5. GDPR & DATA COMPLIANCE
Provider shall process all personal data in accordance with GDPR Article 28.
Data processing agreements will be executed separately. Data retention is
limited to 90 days post-contract.

6. GOVERNING LAW
This agreement shall be governed by the laws of England and Wales.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="ARIA demo runner")
    parser.add_argument("--failure",  action="store_true", help="Simulate a failure + recovery")
    parser.add_argument("--contract", type=str, default=None, help="Path to contract .txt file")
    parser.add_argument("--json",     action="store_true", help="Dump raw JSON result")
    args = parser.parse_args()

    # ── Banner ────────────────────────────────────────────────────
    print(f"\n{BOLD}{CYAN}")
    print("  ⬡  ARIA — Autonomous Reliability & Intelligence Architecture")
    print("     Self-healing Enterprise Contract Intelligence")
    print(f"{RESET}")

    # ── Load contract ─────────────────────────────────────────────
    if args.contract:
        with open(args.contract) as f:
            contract_text = f.read()
        print(f"  {GREEN}✓{RESET}  Contract loaded: {args.contract} ({len(contract_text):,} chars)")
    else:
        contract_text = SAMPLE_CONTRACT
        print(f"  {DIM}Using built-in sample contract ({len(contract_text):,} chars){RESET}")

    if args.failure:
        print(f"  {YELLOW}⚠  Failure simulation enabled{RESET}")

    # ── Try real backend ──────────────────────────────────────────
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"  {GREEN}✓{RESET}  API key detected — LLM reasoning enabled")
    else:
        print(f"  {DIM}No API key — running in demo mode (all logic active){RESET}")

    print()

    # ── Run ARIA ──────────────────────────────────────────────────
    t0 = time.perf_counter()
    try:
        from agents.orchestrator import ARIAOrchestrator
        orch   = ARIAOrchestrator(api_key=api_key, threshold=0.70)
        result = orch.run(contract_text, simulate_failure=args.failure)
    except Exception as exc:
        print(f"  {YELLOW}Backend unavailable ({exc}) — using mock result{RESET}")
        result = _mock_result(args.failure)

    elapsed = time.perf_counter() - t0

    # ── Print results ─────────────────────────────────────────────
    status_colour = GREEN if result["status"] == "success" else YELLOW
    header("WORKFLOW RESULT")
    kv("Status",        result["status"].upper(),  status_colour)
    kv("Reliability",   f"{result['reliability']:.4f}", CYAN)
    kv("Self-healed",   str(result.get("failed", False)), YELLOW if result.get("failed") else DIM)
    kv("Recovery strat",result.get("recovery_strategy") or "—", YELLOW)
    kv("Elapsed",       f"{elapsed:.2f}s", DIM)

    header("CLAUSE ANALYSIS")
    for c in result.get("clauses", [])[:6]:
        risk_col = RED if c["risk"] == "HIGH" else YELLOW if c["risk"] == "MEDIUM" else GREEN
        print(f"  {risk_col}{c['risk']:<8}{RESET}  {c['clause']:<28} {DIM}{c['status']}{RESET}")
        print(f"  {DIM}{'':8}  💡 {c['suggestion']}{RESET}")

    header("RISK SCORES")
    for dim, score in sorted(result.get("risks", {}).items(), key=lambda x: -x[1]):
        bar_len = int(score * 30)
        bar_col = RED if score > 0.65 else YELLOW if score > 0.40 else GREEN
        bar = f"{bar_col}{'█' * bar_len}{'░' * (30 - bar_len)}{RESET}"
        print(f"  {dim:<20} {bar}  {score:.2f}")

    header("EXECUTION LOG")
    level_col = {"info": DIM, "success": GREEN, "warning": YELLOW, "error": RED}
    for log in result.get("logs", []):
        col = level_col.get(log.get("level", "info"), DIM)
        print(f"  {DIM}{log.get('timestamp',''):>10}{RESET}  {CYAN}{log.get('agent',''):>14}{RESET}  {col}{log.get('message','')}{RESET}")

    header("IMPACT SUMMARY")
    imp = result.get("impact", {})
    kv("Risk items found",        str(imp.get("risk_items_found", 0)),         RED)
    kv("Liability exposure (est)",imp.get("estimated_liability_exposure", "—"), RED)
    kv("Compliance flags",        str(imp.get("compliance_issues", 0)),         YELLOW)
    kv("Time saved",              f"{imp.get('time_saved_hrs', 0)} hours",       GREEN)

    if result.get("llm_summary"):
        header("AI SUMMARY")
        # Word-wrap to 70 chars
        words = result["llm_summary"].replace("**", "").split()
        line, lines = [], []
        for w in words:
            line.append(w)
            if sum(len(x) + 1 for x in line) > 68:
                lines.append(" ".join(line[:-1]))
                line = [w]
        if line:
            lines.append(" ".join(line))
        for l in lines:
            print(f"  {l}")

    if args.json:
        header("RAW JSON")
        payload = {k: v for k, v in result.items() if k not in ("logs",)}
        print(json.dumps(payload, indent=2))

    print(f"\n{DIM}  ─────────────────────────────────────────────────────────{RESET}")
    print(f"  {CYAN}Run  streamlit run app/streamlit_app.py  for the full UI{RESET}")
    print()


def _mock_result(failure: bool) -> dict:
    """Minimal mock for when the backend is completely unavailable."""
    return {
        "status": "recovered" if failure else "success",
        "reliability": 0.61 if failure else 0.83,
        "failed": failure,
        "recovery_strategy": "simplify_reparse" if failure else None,
        "clauses": [
            {"clause": "Liability Cap",    "status": "⚠ Ambiguous",    "risk": "HIGH",   "suggestion": "Add explicit monetary cap."},
            {"clause": "GDPR Article 28",  "status": "✓ Present",       "risk": "LOW",    "suggestion": "Execute DPA before data transfer."},
            {"clause": "Indemnification",  "status": "⚠ Broad",         "risk": "HIGH",   "suggestion": "Narrow to direct damages only."},
            {"clause": "Force Majeure",    "status": "⚠ Missing Scope", "risk": "MEDIUM", "suggestion": "Add cyber & supply-chain events."},
            {"clause": "Termination",      "status": "✓ Present",       "risk": "LOW",    "suggestion": "Attach fee schedule as Schedule A."},
        ],
        "risks": {"Liability": 0.75, "Termination": 0.50, "Payment": 0.35, "Compliance": 0.60, "Data Privacy": 0.45},
        "logs": [
            {"timestamp": "00:00.000", "agent": "ORCHESTRATOR", "level": "info",    "message": "Workflow initiated"},
            {"timestamp": "00:00.312", "agent": "EXTRACTION",   "level": "info",    "message": "5 clauses extracted"},
            {"timestamp": "00:00.799", "agent": "COMPLIANCE",   "level": "warning" if failure else "success", "message": "Compliance check complete"},
            {"timestamp": "00:01.013", "agent": "RISK",         "level": "info",    "message": "Risk scoring complete"},
            {"timestamp": "00:01.250", "agent": "ORCHESTRATOR", "level": "success", "message": "Workflow complete"},
        ],
        "memory": [],
        "llm_summary": "Demo mode — add ANTHROPIC_API_KEY for real LLM reasoning.",
        "impact": {"risk_items_found": 3, "estimated_liability_exposure": "$420K",
                   "compliance_issues": 2, "time_saved_hrs": 3.5},
    }


if __name__ == "__main__":
    main()
