"""
ARIA — Simulation Runner
Run a Monte Carlo benchmark over N synthetic contracts and print the FTI report.

Usage:
    python -m app.evaluation.simulation
    python -m app.evaluation.simulation --runs 500
"""

from __future__ import annotations
import argparse
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.reliability import ReliabilitySimulator


def main(n_runs: int = 100, verbose: bool = False) -> None:
    print(f"\n⬡  ARIA Reliability Benchmark — {n_runs} synthetic contracts\n")
    print("─" * 60)

    sim    = ReliabilitySimulator()
    report = sim.run(n=n_runs)

    print(f"  Workflow Completion Rate : {report.workflow_completion_rate:.1%}")
    print(f"  Fault Tolerance Index    : {report.fault_tolerance_index:.4f}")
    print(f"  Mean Reliability         : {report.mean_reliability:.4f}  (σ={report.reliability_stddev:.4f})")
    print(f"  Recovery Success Rate    : {report.recovery_success_rate:.1%}")
    print(f"  Mean Recovery Time       : {report.mean_recovery_time_ms:.0f} ms")
    print(f"  P95 Recovery Time        : {report.p95_recovery_time_ms:.0f} ms")
    print("─" * 60)
    print(f"\n  Summary: {report.summary()}\n")

    if verbose:
        print("\n  Detailed run log (first 20):\n")
        for r in report.run_log[:20]:
            status = "HEALED" if r.recovered else ("FAILED" if r.failed else "OK    ")
            strat  = f"  [{r.recovery_strategy}]" if r.recovery_strategy else ""
            print(f"  Run {r.run_id:3d} | {status} | rel={r.reliability:.3f} → {r.final_reliability:.3f}{strat}")

    # Strategy distribution
    strats: dict[str, int] = {}
    for r in report.run_log:
        if r.recovery_strategy:
            strats[r.recovery_strategy] = strats.get(r.recovery_strategy, 0) + 1
    if strats:
        print("\n  Recovery strategy distribution:")
        for s, count in sorted(strats.items(), key=lambda x: -x[1]):
            print(f"    {s:<25} {count:3d}  ({count/sum(strats.values()):.0%})")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARIA simulation benchmark")
    parser.add_argument("--runs",    type=int,  default=100,   help="Number of simulated contracts")
    parser.add_argument("--verbose", action="store_true",      help="Print per-run log")
    args = parser.parse_args()
    main(n_runs=args.runs, verbose=args.verbose)
