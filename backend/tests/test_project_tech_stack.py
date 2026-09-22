import pytest

from app.models import (
    AnalysisStatus,
    Project,
    ProjectAnalysis,
    ProjectStatus,
    TaskPriority,
    Technology,
    User,
    UserRole,
)
from app.orchestration.context import build_project_context
from app.services.project_service import generate_tasks_from_analysis
from app.services.tech_stack import compose_known_technologies
from sqlalchemy import select


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


@pytest.mark.asyncio
async def test_generate_tasks_extracts_stack_from_step_analysis(db_session):
    manager = User(
        email="mgr@example.com",
        hashed_password="x",
        full_name="Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(manager)
    await db_session.flush()

    project = Project(
        name="Phased App",
        idea="Test step-based stack extraction",
        created_by_id=manager.id,
        status=ProjectStatus.APPROVED,
        priority=TaskPriority.MEDIUM,
    )
    db_session.add(project)
    await db_session.flush()

    db_session.add(
        ProjectAnalysis(
            project_id=project.id,
            version_number=1,
            step="delivery_plan",
            payload={
                "tasks": [
                    {
                        "task_id": "T1",
                        "name": "Setup",
                        "description": "Initial setup",
                        "priority": "high",
                        "estimated_effort_days": 2,
                    }
                ]
            },
            status=AnalysisStatus.APPROVED,
        )
    )
    db_session.add(
        ProjectAnalysis(
            project_id=project.id,
            version_number=1,
            step="product_blueprint",
            payload={
                "functional": [],
                "non_functional": [],
            },
            status=AnalysisStatus.APPROVED,
        )
    )
    db_session.add(
        ProjectAnalysis(
            project_id=project.id,
            version_number=1,
            step="solution_architecture",
            payload={
                "stack": [
                    {"category": "frontend", "name": "React", "rationale": "User choice"},
                ],
            },
            status=AnalysisStatus.APPROVED,
        )
    )
    await db_session.flush()

    tasks = await generate_tasks_from_analysis(db_session, project)
    assert len(tasks) == 1

    tech_result = await db_session.execute(
        select(Technology).where(Technology.project_id == project.id)
    )
    technologies = tech_result.scalars().all()
    assert len(technologies) == 1
    assert technologies[0].name == "React"


@pytest.mark.asyncio
async def test_generate_tasks_falls_back_to_data_structure_stack(db_session):
    manager = User(
        email="mgr2@example.com",
        hashed_password="x",
        full_name="Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(manager)
    await db_session.flush()

    project = Project(
        name="Arch App",
        idea="Data structure stack fallback",
        created_by_id=manager.id,
        status=ProjectStatus.APPROVED,
        priority=TaskPriority.MEDIUM,
    )
    db_session.add(project)
    await db_session.flush()

    db_session.add(
        ProjectAnalysis(
            project_id=project.id,
            version_number=1,
            step="implementation_approach",
            payload={"tasks": []},
            status=AnalysisStatus.APPROVED,
        )
    )
    db_session.add(
        ProjectAnalysis(
            project_id=project.id,
            version_number=1,
            step="projects",
            payload={"functional": [], "non_functional": []},
            status=AnalysisStatus.APPROVED,
        )
    )
    db_session.add(
        ProjectAnalysis(
            project_id=project.id,
            version_number=1,
            step="data_structure",
            payload={
                "stack": [
                    {"category": "database", "name": "PostgreSQL", "rationale": "User choice"},
                ]
            },
            status=AnalysisStatus.APPROVED,
        )
    )
    await db_session.flush()

    await generate_tasks_from_analysis(db_session, project)
    tech_result = await db_session.execute(
        select(Technology).where(Technology.project_id == project.id)
    )
    technologies = tech_result.scalars().all()
    assert len(technologies) == 1
    assert technologies[0].name == "PostgreSQL"


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
