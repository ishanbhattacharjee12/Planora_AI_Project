COMPLEXITY_WEIGHTS = {
    "technical": 0.20,
    "security": 0.20,
    "integration": 0.15,
    "ai": 0.15,
    "infrastructure": 0.10,
    "data": 0.10,
    "team": 0.10,
}

LEVEL_MAP = {
    "low": 25,
    "medium": 50,
    "high": 75,
    "very_high": 90,
    "advanced": 85,
    "intermediate": 55,
    "basic": 30,
}


def compute_complexity(factor_assessments: dict[str, str]) -> dict:
    scores: dict[str, float] = {}
    for factor, weight in COMPLEXITY_WEIGHTS.items():
        level = factor_assessments.get(factor, "medium").lower()
        scores[factor] = LEVEL_MAP.get(level, 50)

    overall = sum(scores[k] * COMPLEXITY_WEIGHTS[k] for k in COMPLEXITY_WEIGHTS)
    if overall >= 75:
        label = "Advanced"
    elif overall >= 50:
        label = "Intermediate"
    else:
        label = "Basic"

    return {
        "overall_complexity": label,
        "overall_score": round(overall, 1),
        "factor_scores": {k: round(v, 1) for k, v in scores.items()},
    }
