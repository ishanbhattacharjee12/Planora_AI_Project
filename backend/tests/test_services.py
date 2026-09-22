import pytest

from app.orchestration.complexity import compute_complexity
from app.services.matching_service import (
    availability_score,
    compute_match_score,
    find_skill_gaps,
    recommendation_label,
    skill_match_score,
)
from app.ai.validators.sensitive_data import scan_sensitive_data


def test_complexity_scoring():
    result = compute_complexity({
        "technical": "high",
        "security": "very_high",
        "integration": "medium",
        "ai": "high",
        "infrastructure": "low",
        "data": "medium",
        "team": "low",
    })
    assert result["overall_complexity"] in {"Basic", "Intermediate", "Advanced"}
    assert 0 < result["overall_score"] <= 100


def test_skill_match_score():
    required = {"Python": "advanced", "React": "intermediate"}
    employee = {"Python": "advanced", "React": "beginner"}
    score = skill_match_score(required, employee)
    assert 0 < score < 100


def test_skill_match_perfect():
    required = {"Python": "intermediate"}
    employee = {"Python": "advanced"}
    assert skill_match_score(required, employee) == 100.0


def test_availability_score():
    assert availability_score(40, 100) == 60.0
    assert availability_score(100, 100) == 0.0


def test_compute_match_score():
    score = compute_match_score(90, 80, 70)
    assert score > 0


def test_recommendation_label():
    assert recommendation_label(90, 50) == "Recommended"
    assert recommendation_label(60, 50) == "Possible"


def test_find_skill_gaps():
    gaps = find_skill_gaps({"Docker": "intermediate"}, {"Docker": "beginner"})
    assert len(gaps) == 1
    assert gaps[0]["skill"] == "Docker"


def test_sensitive_data_scanner_detects_api_key():
    result = scan_sensitive_data("api_key=sk-abcdefghijklmnopqrstuvwxyz123456")
    assert result.has_sensitive


def test_sensitive_data_scanner_clean_text():
    result = scan_sensitive_data("Build a vulnerability management platform")
    assert not result.has_sensitive
