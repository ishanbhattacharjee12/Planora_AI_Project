import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token
from app.database import get_db
from app.main import app
from app.models import (
    AIRequest,
    AIResponse,
    AssistantMessage,
    Document,
    DocumentChunk,
    OrchestrationRun,
    Project,
    ProjectAnalysis,
    ProjectMemoryLog,
    ProjectVersion,
    Requirement,
    Task,
    TaskDependency,
    Technology,
    User,
)
from app.services.tech_stack import compose_known_technologies


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def authed_client(db_session: AsyncSession, manager_user: User):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(manager_user.id, manager_user.role)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_project_with_tech_stack(authed_client):
    response = await authed_client.post(
        "/api/projects",
        json={
            "name": "Stack Test",
            "idea": "A sample app",
            "frontend_technology": "react",
            "backend_technology": "node_express",
            "database_technology": "postgresql",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["frontend_technology"] == "react"
    assert data["backend_technology"] == "node_express"
    assert data["database_technology"] == "postgresql"
    assert data["known_technologies"] == compose_known_technologies(
        "react", "node_express", "postgresql"
    )

    logs_response = await authed_client.get("/api/logs")
    assert logs_response.status_code == 200
    logs = logs_response.json()
    assert logs[0]["project_id"] == data["id"]
    assert "Frontend: React" in logs[0]["architecture"]

    similar_response = await authed_client.post(
        "/api/logs/similar",
        json={
            "name": "Another Stack Test",
            "idea": "A sample app",
            "frontend_technology": "react",
            "backend_technology": "node_express",
            "database_technology": "postgresql",
        },
    )
    assert similar_response.status_code == 200
    assert similar_response.json()[0]["project_id"] == data["id"]


@pytest.mark.asyncio
async def test_delete_project_removes_all_related_records(
    authed_client, db_session: AsyncSession, manager_user: User
):
    create_response = await authed_client.post(
        "/api/projects",
        json={"name": "Temporary Project", "idea": "Delete this test project"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    first_task = Task(project_id=project_id, task_id="TASK-1", name="First task")
    second_task = Task(project_id=project_id, task_id="TASK-2", name="Second task")
    document = Document(
        title="Temporary brief",
        filename="temporary.txt",
        file_path="uploads/temporary.txt",
        project_id=project_id,
        uploaded_by_id=manager_user.id,
    )
    ai_request = AIRequest(user_id=manager_user.id, project_id=project_id, request_type="analysis", model="test")
    db_session.add_all([
        ProjectAnalysis(project_id=project_id, step="product_blueprint", payload={"overview": "test"}),
        Requirement(project_id=project_id, req_id="REQ-1", description="Test requirement"),
        Technology(project_id=project_id, category="frontend", name="React"),
        first_task,
        second_task,
        ProjectVersion(project_id=project_id, version_number=1, snapshot={"name": "Temporary Project"}, created_by_id=manager_user.id),
        document,
        ai_request,
        OrchestrationRun(project_id=project_id),
        AssistantMessage(project_id=project_id, user_id=manager_user.id, role="user", content="test"),
    ])
    await db_session.flush()
    db_session.add_all([
        TaskDependency(task_id=second_task.id, depends_on_task_id=first_task.id),
        DocumentChunk(document_id=document.id, project_id=project_id, chunk_index=0, content="test"),
        AIResponse(request_id=ai_request.id, content="test"),
    ])
    await db_session.flush()

    delete_response = await authed_client.delete(f"/api/projects/{project_id}")
    assert delete_response.status_code == 204

    logs_response = await authed_client.get("/api/logs")
    assert all(log["project_id"] != project_id for log in logs_response.json())
    for model in (
        Project,
        ProjectMemoryLog,
        ProjectAnalysis,
        Requirement,
        Technology,
        Task,
        TaskDependency,
        ProjectVersion,
        Document,
        DocumentChunk,
        AIRequest,
        AIResponse,
        OrchestrationRun,
        AssistantMessage,
    ):
        count = await db_session.scalar(select(func.count()).select_from(model))
        assert count == 0, f"{model.__name__} records were not deleted"
