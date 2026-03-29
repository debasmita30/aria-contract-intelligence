def apply_rules(text):
    """
    Mock rules engine
    """
    if "ambiguous" in text:
        return "Flagged: Ambiguity detected"
    return "No issues"