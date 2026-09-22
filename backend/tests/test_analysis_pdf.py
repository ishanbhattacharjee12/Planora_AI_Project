from types import SimpleNamespace

from app.orchestration.state import STEP_ORDER
from app.services.analysis_pdf import analysis_pdf_filename, build_analysis_pdf


def _sample_project() -> SimpleNamespace:
    return SimpleNamespace(
        name="Food Delivery App",
        idea="On-demand food delivery for urban customers.",
        description="Mobile-first ordering platform.",
        business_objective="Launch MVP in 90 days.",
        organization="Random Trees",
        document_type="Functional Documentation",
        primary_users="DE Leadership, Delivery Leads, Project Managers",
        how_to_read=None,
        current_version=1,
        status=SimpleNamespace(value="review"),
    )


def _sample_analyses() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            step="executive_dashboard",
            confidence="high",
            payload={
                "overview": "Executive overview for the delivery app.",
                "kpi_cards": [
                    {
                        "name": "Order Volume",
                        "description": "Daily completed orders",
                        "metric": "1,200/day",
                        "target": "2,000/day",
                    }
                ],
                "drill_downs": ["Orders", "Restaurants"],
                "filters": ["City", "Date range"],
                "recommended_widgets": ["Live order map"],
            },
        ),
        SimpleNamespace(
            step="implementation_approach",
            confidence="medium",
            payload={
                "overview": "Phased delivery plan.",
                "phases": [{"phase": "1", "name": "MVP", "description": "Core ordering flow"}],
                "sprint_focus": ["Auth", "Checkout"],
                "tasks": [
                    {
                        "task_id": "T-001",
                        "name": "Build checkout API",
                        "description": "Create payment and order submission endpoints.",
                        "priority": "high",
                        "estimated_effort_days": 5,
                        "difficulty": "medium",
                        "required_skills": {"Python": "advanced"},
                        "dependencies": [],
                    }
                ],
            },
        ),
        SimpleNamespace(
            step="closing_note",
            confidence="high",
            payload={
                "overview": "Close with next steps.",
                "vision_alignment": "Aligns with rapid MVP launch.",
                "first_deliverables": ["Customer app", "Restaurant portal"],
                "recommended_next_decision": "Approve MVP scope.",
            },
        ),
    ]


def test_build_analysis_pdf_returns_pdf_bytes():
    pdf = build_analysis_pdf(_sample_project(), _sample_analyses())
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_analysis_pdf_filename_is_safe():
    project = _sample_project()
    assert analysis_pdf_filename(project) == "Food-Delivery-App-analysis-v1.pdf"


def test_pdf_builder_includes_all_sections_in_order():
    analyses = [
        SimpleNamespace(step=step, confidence="medium", payload={"overview": f"Section {step}"})
        for step in STEP_ORDER
    ]
    pdf = build_analysis_pdf(_sample_project(), analyses)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 5000


def test_pdf_builder_handles_empty_document_metadata():
    project = SimpleNamespace(
        name="Minimal Project",
        idea="Basic idea.",
        description=None,
        business_objective=None,
        organization=None,
        document_type="Functional Documentation",
        primary_users=None,
        how_to_read=None,
        current_version=1,
        status=SimpleNamespace(value="draft"),
    )
    analyses = [
        SimpleNamespace(step="executive_dashboard", confidence="medium", payload={"overview": "Overview"}),
    ]
    pdf = build_analysis_pdf(project, analyses)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500
