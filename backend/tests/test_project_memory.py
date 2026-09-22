from app.services.project_memory import build_project_memory, _keyword_similarity


def test_build_project_memory_contains_summary_and_architecture():
    memory = build_project_memory(
        name="Student Grade Calculator",
        idea="Calculate grades and cumulative GPA for university students.",
        description="A self-service academic calculator.",
        frontend_technology="react",
        backend_technology="fastapi",
        database_technology="sqlite",
    )

    assert memory["snippet"].startswith("Calculate grades")
    assert memory["summary"] == "A self-service academic calculator."
    assert "Frontend: React" in memory["architecture"]
    assert "Student Grade Calculator" in memory["semantic_summary"]


def test_keyword_fallback_finds_near_duplicate_ideas():
    first = "Student portal that calculates grades and cumulative GPA"
    second = "A GPA and grade calculator portal for university students"
    assert _keyword_similarity(first, second) >= 0.5


def test_keyword_fallback_rejects_unrelated_ideas():
    assert _keyword_similarity(
        "Student GPA calculator",
        "Warehouse inventory and shipment tracking",
    ) == 0
