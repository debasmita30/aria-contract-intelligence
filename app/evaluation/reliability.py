"""
ARIA — Evaluation Module: Reliability & FTI Scoring
Simulates production workloads and computes:
  - Fault Tolerance Index (FTI)
  - Mean Time To Recovery (MTTR)
  - Recovery Success Rate
  - Workflow Completion Rate
"""

from __future__ import annotations
import random
import math
import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimulationRun:
    run_id:            int
    reliability:       float
    failed:            bool
    recovered:         bool
    recovery_strategy: str | None
    recovery_time_ms:  int
    final_reliability: float


@dataclass
class EvaluationReport:
    n_runs:                   int
    workflow_completion_rate: float   # % runs that produced usable output
    fault_tolerance_index:    float   # FTI — see formula below
    mean_reliability:         float
    reliability_stddev:       float
    recovery_success_rate:    float   # % of failed runs that self-healed
    mean_recovery_time_ms:    float
    p95_recovery_time_ms:     float
    run_log:                  list[SimulationRun] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"Runs: {self.n_runs} | "
            f"Completion: {self.workflow_completion_rate:.1%} | "
            f"FTI: {self.fault_tolerance_index:.3f} | "
            f"μ Reliability: {self.mean_reliability:.3f} | "
            f"Recovery: {self.recovery_success_rate:.1%} | "
            f"MTTR: {self.mean_recovery_time_ms:.0f}ms"
        )


class ReliabilitySimulator:
    """
    Monte Carlo simulation of ARIA's reliability across N synthetic contracts.

    FTI (Fault Tolerance Index):
        FTI = (completed_runs / total_runs) × (1 + recovery_rate × 0.5)
        
        - Rewards systems that complete despite failures
        - Bonus for high autonomous recovery rate
        - Range [0, 1.5]; normalise to [0, 1] for display
    """

    def __init__(
        self,
        threshold:         float = 0.70,
        base_reliability:  float = 0.80,
        failure_rate:      float = 0.18,   # 18% of contracts trigger recovery
        recovery_rate:     float = 0.94,   # 94% of failures are self-healed
        seed:              int   = 42,
    ):
        self.threshold        = threshold
        self.base_reliability = base_reliability
        self.failure_rate     = failure_rate
        self.recovery_rate    = recovery_rate
        random.seed(seed)

    def run(self, n: int = 100) -> EvaluationReport:
        runs: list[SimulationRun] = []
        strategies = ["simplify_reparse", "confidence_boost", "decompose", "rule_based_fallback"]

        for i in range(n):
            # Simulate raw reliability draw
            rel = random.gauss(self.base_reliability, 0.12)
            rel = max(0.1, min(0.99, rel))
            failed = rel < self.threshold

            recovered         = False
            recovery_strategy = None
            recovery_ms       = 0
            final_rel         = rel

            if failed:
                recovered = random.random() < self.recovery_rate
                if recovered:
                    recovery_strategy = random.choice(strategies)
                    recovery_ms       = int(random.gauss(380, 80))
                    # Recovery boosts reliability
                    boost     = random.uniform(0.08, 0.18)
                    final_rel = min(0.98, rel + boost)

            runs.append(SimulationRun(
                run_id            = i + 1,
                reliability       = round(rel, 4),
                failed            = failed,
                recovered         = recovered,
                recovery_strategy = recovery_strategy,
                recovery_time_ms  = recovery_ms,
                final_reliability = round(final_rel, 4),
            ))

        return self._compute_report(runs)

    def _compute_report(self, runs: list[SimulationRun]) -> EvaluationReport:
        n = len(runs)
        failed_runs    = [r for r in runs if r.failed]
        recovered_runs = [r for r in failed_runs if r.recovered]
        completed_runs = [r for r in runs if not r.failed or r.recovered]

        final_rels  = [r.final_reliability for r in runs]
        rec_times   = [r.recovery_time_ms  for r in recovered_runs] or [0]

        completion_rate   = len(completed_runs) / n
        recovery_rate     = len(recovered_runs) / max(1, len(failed_runs))
        mean_rel          = statistics.mean(final_rels)
        rel_std           = statistics.stdev(final_rels) if n > 1 else 0.0
        mttr              = statistics.mean(rec_times)
        rec_times_sorted  = sorted(rec_times)
        p95_idx           = int(math.ceil(0.95 * len(rec_times_sorted))) - 1
        p95_mttr          = rec_times_sorted[max(0, p95_idx)]

        # FTI formula
        raw_fti = completion_rate * (1 + recovery_rate * 0.5)
        fti     = min(1.0, raw_fti / 1.5)   # normalise to [0,1]

        return EvaluationReport(
            n_runs                   = n,
            workflow_completion_rate = round(completion_rate, 4),
            fault_tolerance_index    = round(fti, 4),
            mean_reliability         = round(mean_rel, 4),
            reliability_stddev       = round(rel_std, 4),
            recovery_success_rate    = round(recovery_rate, 4),
            mean_recovery_time_ms    = round(mttr, 1),
            p95_recovery_time_ms     = float(p95_mttr),
            run_log                  = runs,
        )


class FTIScorer:
    """
    Standalone FTI computation for a set of pre-existing run results.
    Use this to evaluate a live ARIA deployment.
    """

    @staticmethod
    def score(run_results: list[dict]) -> dict[str, float]:
        n = len(run_results)
        if n == 0:
            return {"fti": 0.0, "completion_rate": 0.0, "recovery_rate": 0.0}

        failed    = [r for r in run_results if r.get("failed")]
        recovered = [r for r in failed     if r.get("status") == "recovered"]
        completed = [r for r in run_results if r.get("status") in ("success", "recovered")]

        completion_rate = len(completed) / n
        recovery_rate   = len(recovered) / max(1, len(failed))
        raw_fti         = completion_rate * (1 + recovery_rate * 0.5)
        fti             = min(1.0, raw_fti / 1.5)

        reliabilities = [r.get("reliability", 0) for r in run_results]
        mean_rel      = sum(reliabilities) / n if reliabilities else 0

        return {
            "fti":             round(fti, 4),
            "completion_rate": round(completion_rate, 4),
            "recovery_rate":   round(recovery_rate, 4),
            "mean_reliability":round(mean_rel, 4),
        }
