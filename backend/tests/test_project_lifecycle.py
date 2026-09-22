import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password
from app.database import get_db
from app.main import app
from app.models import Project, ProjectStatus, Task, TaskStatus, User, UserRole


@pytest_asyncio.fixture
async def employee_user(db_session: AsyncSession):
    user = User(
        email="employee@test.com",
        hashed_password=hash_password("secret"),
        full_name="Test Employee",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def other_manager(db_session: AsyncSession):
    user = User(
        email="other_manager@test.com",
        hashed_password=hash_password("secret"),
        full_name="Other Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.flush()
    return user


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


@pytest_asyncio.fixture
async def employee_client(db_session: AsyncSession, employee_user: User):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(employee_user.id, employee_user.role)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def other_manager_client(db_session: AsyncSession, other_manager: User):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(other_manager.id, other_manager.role)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_project_status_lifecycle_updates(authed_client, db_session: AsyncSession):
    # 1. Create project (starts in draft)
    create_resp = await authed_client.post(
        "/api/projects",
        json={"name": "Lifecycle Project", "idea": "Test lifecycle status changes"},
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "draft"

    # 2. Update to in_progress
    patch_resp = await authed_client.patch(
        f"/api/projects/{project_id}",
        json={"status": "in_progress"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "in_progress"

    # 3. Update to completed
    complete_resp = await authed_client.patch(
        f"/api/projects/{project_id}",
        json={"status": "completed"},
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"

    # 4. Update to overdue
    overdue_resp = await authed_client.patch(
        f"/api/projects/{project_id}",
        json={"status": "overdue"},
    )
    assert overdue_resp.status_code == 200
    assert overdue_resp.json()["status"] == "overdue"

    # 5. Fetch project detail and verify persisted status in database
    detail_resp = await authed_client.get(f"/api/projects/{project_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == "overdue"


@pytest.mark.asyncio
async def test_invalid_status_value_rejected(authed_client):
    create_resp = await authed_client.post(
        "/api/projects",
        json={"name": "Validation Project", "idea": "Test invalid status"},
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    invalid_resp = await authed_client.patch(
        f"/api/projects/{project_id}",
        json={"status": "unknown_invalid_status"},
    )
    assert invalid_resp.status_code == 422


@pytest.mark.asyncio
async def test_unauthorized_users_cannot_update_project_status(
    employee_client, other_manager_client, authed_client
):
    create_resp = await authed_client.post(
        "/api/projects",
        json={"name": "Manager Project", "idea": "Non-members cannot edit"},
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    # Employee should be forbidden (403)
    emp_patch_resp = await employee_client.patch(
        f"/api/projects/{project_id}",
        json={"status": "completed"},
    )
    assert emp_patch_resp.status_code == 403

    # Other non-member manager should be forbidden (403)
    other_patch_resp = await other_manager_client.patch(
        f"/api/projects/{project_id}",
        json={"status": "completed"},
    )
    assert other_patch_resp.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_stats_reflect_project_lifecycle_and_tasks(
    authed_client, db_session: AsyncSession
):
    # Create project 1 -> mark in_progress
    p1_resp = await authed_client.post(
        "/api/projects",
        json={"name": "Project One", "idea": "P1"},
    )
    p1_id = p1_resp.json()["id"]
    await authed_client.patch(f"/api/projects/{p1_id}", json={"status": "in_progress"})

    # Create project 2 -> mark completed
    p2_resp = await authed_client.post(
        "/api/projects",
        json={"name": "Project Two", "idea": "P2"},
    )
    p2_id = p2_resp.json()["id"]
    await authed_client.patch(f"/api/projects/{p2_id}", json={"status": "completed"})

    # Create project 3 -> mark overdue
    p3_resp = await authed_client.post(
        "/api/projects",
        json={"name": "Project Three", "idea": "P3"},
    )
    p3_id = p3_resp.json()["id"]
    await authed_client.patch(f"/api/projects/{p3_id}", json={"status": "overdue"})

    # Add 2 pending tasks to Project 1
    db_session.add(
        Task(project_id=p1_id, task_id="TASK-001", name="Task 1", status=TaskStatus.TODO)
    )
    db_session.add(
        Task(project_id=p1_id, task_id="TASK-002", name="Task 2", status=TaskStatus.IN_PROGRESS)
    )
    # Add 1 completed task to Project 1
    db_session.add(
        Task(project_id=p1_id, task_id="TASK-003", name="Task 3", status=TaskStatus.DONE)
    )
    await db_session.flush()

    # Query dashboard stats
    stats_resp = await authed_client.get("/api/dashboard/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()

    assert stats["total_projects"] == 3
    assert stats["active_projects"] == 1
    assert stats["completed_projects"] == 1
    assert stats["overdue_projects"] == 1
    # Tasks: only pending (todo + in_progress = 2)
    assert stats["pending_tasks"] == 2
