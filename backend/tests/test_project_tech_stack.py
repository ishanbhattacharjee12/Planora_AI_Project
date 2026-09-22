import pytest

from app.models import (
    Project,
    ProjectStatus,
    TaskPriority,
)
from app.orchestration.context import build_project_context
from app.services.tech_stack import compose_known_technologies


def test_compose_known_technologies():
    result = compose_known_technologies("react", "python_fastapi", "postgresql")
    assert result == "Frontend: React | Backend: Python (FastAPI) | Database: PostgreSQL"


def test_compose_known_technologies_partial():
    assert compose_known_technologies("react", None, None) == "Frontend: React"
    assert compose_known_technologies(None, None, None) == ""


def test_build_project_context_includes_tech_stack():
    project = Project(
        id=1,
        name="Test App",
        idea="A task manager",
        frontend_technology="react",
        backend_technology="node_express",
        database_technology="postgresql",
        created_by_id=1,
        status=ProjectStatus.DRAFT,
        priority=TaskPriority.MEDIUM,
    )
    context = build_project_context(project)
    assert "Preferred Tech Stack" in context
    assert "Frontend: React" in context
    assert "Backend: Node.js (Express)" in context
    assert "Database: PostgreSQL" in context
    assert "MUST honor" in context


def test_build_project_context_falls_back_to_known_technologies():
    project = Project(
        id=1,
        name="Legacy",
        idea="An app",
        known_technologies="Frontend: Vue.js | Backend: Go",
        created_by_id=1,
        status=ProjectStatus.DRAFT,
        priority=TaskPriority.MEDIUM,
    )
    context = build_project_context(project)
    assert "Known Technologies: Frontend: Vue.js | Backend: Go" in context
    assert "Preferred Tech Stack" not in context
