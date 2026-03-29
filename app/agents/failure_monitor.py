import math

class BayesianFailureMonitor:

    def __init__(self, threshold=0.7):
        self.threshold = threshold

    def compute_reliability(self, state):
        """
        Compute reliability from actual agent outputs
        """
        scores = []

        for name, result in state.agent_results.items():
            if isinstance(result, dict):
                scores.append(result.get("confidence", 0.7))

        if not scores:
            return 0.0

        # Geometric mean → realistic multi-agent reliability
        product = 1.0
        for s in scores:
            product *= max(0.01, s)

        geom_mean = product ** (1 / len(scores))

        # Penalize ambiguity in input
        text = state.input_text.lower()
        penalty = 0

        if "ambiguous" in text or "unclear" in text:
            penalty += 0.15

        if len(text) > 300:
            penalty += 0.05

        reliability = max(0, geom_mean - penalty)

        return round(reliability, 3)

    def check(self, reliability, state):
        """
        Decide failure + give explainable reason
        """
        scores = [
            r.get("confidence", 0.7)
            for r in state.agent_results.values()
            if isinstance(r, dict)
        ]

        variance = self._variance(scores)

        hard_fail = reliability < self.threshold
        disagreement = variance > 0.04

        failed = hard_fail or (disagreement and reliability < 0.75)

        reason = self._reason(reliability, variance, state)

        return failed, {
            "reliability": reliability,
            "variance": round(variance, 3),
            "reason": reason,
            "worst_agent": self._worst_agent(state)
        }

    def _worst_agent(self, state):
        worst = None
        lowest = 1.0

        for name, r in state.agent_results.items():
            if isinstance(r, dict):
                c = r.get("confidence", 1.0)
                if c < lowest:
                    lowest = c
                    worst = name

        return worst

    def _variance(self, scores):
        if len(scores) < 2:
            return 0.0
        mean = sum(scores) / len(scores)
        return sum((s - mean) ** 2 for s in scores) / len(scores)

    def _reason(self, reliability, variance, state):
        if reliability < 0.4:
            return "critical_failure"
        if variance > 0.06:
            return "agent_disagreement"
        if "ambiguous" in state.input_text.lower():
            return "ambiguity"
        return "low_confidence"