from app.models import Project, ProjectStatus, TaskPriority
from app.orchestration.context import build_project_context
from app.orchestration.state import STEP_ORDER, STEP_SCHEMAS, WORKFLOW_STEPS


def test_workflow_has_five_focused_steps():
    assert len(WORKFLOW_STEPS) == 5
    assert STEP_ORDER == [name for name, _, _ in WORKFLOW_STEPS]


def test_workflow_step_names_cover_the_delivery_lifecycle():
    expected = [
        "product_blueprint",
        "solution_architecture",
        "delivery_plan",
        "team_operations",
        "launch_growth",
    ]
    assert [name for name, _, _ in WORKFLOW_STEPS] == expected
    assert set(STEP_SCHEMAS) == set(expected)


def test_build_project_context_includes_stack_fields():
    project = Project(
        id=1,
        name="Shop",
        idea="E-commerce platform",
        frontend_technology="nextjs",
        backend_technology="python_django",
        database_technology="mysql",
        created_by_id=1,
        status=ProjectStatus.DRAFT,
        priority=TaskPriority.MEDIUM,
    )
    context = build_project_context(project, prior={"product_blueprint": {"overview": "done"}})
    assert "Frontend: Next.js" in context
    assert "Backend: Python (Django)" in context
    assert "Database: MySQL" in context
    assert "Prior Analysis" in context


def test_legacy_step_names_removed():
    legacy = {
        "project_summary",
        "requirements",
        "technology",
        "skills",
        "complexity_factors",
        "effort",
        "roadmap",
        "risks",
        "tasks",
        "foundation",
        "workforce",
        "platform",
        "delivery",
    }
    current = {name for name, _, _ in WORKFLOW_STEPS}
    assert legacy.isdisjoint(current)
