def choose_strategy(state):
    failure_type = state.get("failure_reason", "")

    if "ambiguity" in failure_type:
        return "simplify"

    if "low_confidence" in failure_type:
        return "retry"

    return "rule_based"