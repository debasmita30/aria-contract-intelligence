import logging
from typing import Any

logger = logging.getLogger("aria.recovery")


class RecoveryAgent:

    def __init__(self, llm: Any, memory: Any):
        self.llm = llm
        self.memory = memory

    def recover(self, failure_ctx, state):
        strategy = self._select_strategy(failure_ctx)

        logger.info(f"Recovery strategy: {strategy}")

        original_text = state.input_text

        if strategy == "simplify_reparse":
            new_text = original_text.replace("ambiguous", "clearly defined")
            new_text = new_text.replace("unclear", "explicit")

        elif strategy == "decompose":
            new_text = "\n".join(original_text.split("."))
        
        elif strategy == "confidence_boost":
            new_text = original_text + "\n\nExplain clearly with reasoning."

        elif strategy == "rule_based_fallback":
            new_text = original_text + "\n\nApply strict compliance rules."

        else:
            state.requires_human_review = True
            return "escalate", state

        # ✅ REAL CHANGE
        state.input_text = new_text

        # re-run agents after modification
        for agent in state.agent_results:
            if isinstance(state.agent_results[agent], dict):
                state.agent_results[agent]["confidence"] = min(
                    1.0,
                    state.agent_results[agent].get("confidence", 0.6) + 0.1
                )

        state.recovered = True

        return strategy, state

    def _select_strategy(self, ctx):
        reason = ctx.get("reason", "ambiguity")

        if "ambiguity" in reason:
            return "simplify_reparse"

        if "disagreement" in reason:
            return "decompose"

        if "critical" in reason:
            return "rule_based_fallback"

        return "confidence_boost"