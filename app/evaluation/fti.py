def compute_fti(reliability_scores, threshold=0.7):
    """
    Failure Threshold Index:
    First point where reliability drops below threshold.
    """
    for i, score in enumerate(reliability_scores):
        if score < threshold:
            return i + 1  # complexity level
    return None


def classify_region(score, threshold=0.7):
    if score >= threshold:
        return "Stable"
    return "Unstable"