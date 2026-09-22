SKILL_LEVEL_SCORE = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}


def skill_match_score(required: dict, employee_skills: dict[str, str]) -> float:
    if not required:
        return 100.0
    total = 0.0
    matched = 0.0
    for skill, level in required.items():
        req_score = SKILL_LEVEL_SCORE.get(str(level).lower(), 2)
        emp_score = SKILL_LEVEL_SCORE.get(employee_skills.get(skill, "").lower(), 0)
        total += req_score
        matched += min(emp_score, req_score)
    return round((matched / total) * 100, 1) if total else 100.0


def availability_score(workload_percent: float, capacity_percent: int = 100) -> float:
    if capacity_percent <= 0:
        return 0.0
    available = max(0, capacity_percent - workload_percent)
    return round((available / capacity_percent) * 100, 1)


def compute_match_score(
    skill_match: float,
    experience_relevance: float,
    availability: float,
    past_project_bonus: float = 0.0,
) -> float:
    return round(
        0.50 * skill_match
        + 0.25 * experience_relevance
        + 0.15 * availability
        + 0.10 * past_project_bonus,
        1,
    )


def recommendation_label(score: float, workload: float) -> str:
    if score >= 85 and workload < 80:
        return "Recommended"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Possible"
    return "Not Recommended"


def find_skill_gaps(required: dict, employee_skills: dict[str, str]) -> list[dict[str, str]]:
    gaps = []
    for skill, level in required.items():
        emp_level = employee_skills.get(skill)
        req_score = SKILL_LEVEL_SCORE.get(str(level).lower(), 2)
        emp_score = SKILL_LEVEL_SCORE.get(str(emp_level or "").lower(), 0)
        if emp_score < req_score:
            gaps.append({
                "skill": skill,
                "required_level": str(level),
                "current_level": emp_level or "none",
            })
    return gaps
