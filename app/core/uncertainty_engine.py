"""
ARIA — Uncertainty Engine
Computes Bayesian confidence intervals for agent scores.
"""

from __future__ import annotations
import math

try:
    from scipy.stats import beta as beta_dist
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class UncertaintyEngine:
    """
    Produces 95% credible intervals for each agent score
    using Beta posterior updating.
    """

    PRIOR_ALPHA = 4.0
    PRIOR_BETA  = 2.0

    def compute_bands(self, confidence_scores: dict[str, float]) -> dict[str, dict]:
        bands = {}
        for agent, score in confidence_scores.items():
            alpha = self.PRIOR_ALPHA + score
            b     = self.PRIOR_BETA  + (1.0 - score)
            mean  = alpha / (alpha + b)
            var   = (alpha * b) / ((alpha + b) ** 2 * (alpha + b + 1))

            if SCIPY_AVAILABLE:
                ci_low, ci_high = beta_dist.interval(0.95, alpha, b)
            else:
                std     = math.sqrt(var)
                ci_low  = max(0.0, mean - 1.96 * std)
                ci_high = min(1.0, mean + 1.96 * std)

            bands[agent] = {
                "mean":    round(mean,    3),
                "ci_low":  round(ci_low,  3),
                "ci_high": round(ci_high, 3),
                "variance":round(var,     4),
            }
        return bands
