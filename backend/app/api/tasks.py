from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RequireManager, get_current_user
from app.database import get_db
from app.models import Task, TaskStatus, User
from app.schemas import TaskAssignRequest, TaskCreate, TaskResponse, TaskUpdate
from app.services.audit_service import log_audit
from app.services.project_service import user_can_access_project

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/project/{project_id}", response_model=list[TaskResponse])
async def list_project_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await user_can_access_project(db, user, project_id):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(select(Task).where(Task.project_id == project_id).order_by(Task.id))
    return result.scalars().all()


@router.post("/project/{project_id}", response_model=TaskResponse, status_code=201)
async def create_task(
    project_id: int,
    body: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    count = (await db.execute(select(Task).where(Task.project_id == project_id))).scalars().all()
    task = Task(
        project_id=project_id,
        task_id=f"TASK-{len(count)+1:03d}",
        **body.model_dump(),
    )
    db.add(task)
    await db.flush()
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    body: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if user.role.value == "employee" and task.assignee_id != user.id:
        raise HTTPException(status_code=403, detail="Not your task")
    for key, value in body.model_dump(exclude_unset=True).items():
        if user.role.value == "employee" and key not in {"status"}:
            continue
        setattr(task, key, value)
    await db.flush()
    return task


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    body: TaskAssignRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    task = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.assignee_id = body.assignee_id
    if body.deadline:
        task.deadline = body.deadline
    await log_audit(db, user_id=user.id, action="assign_task", resource_type="task", resource_id=task.id)
    await db.flush()
    await db.refresh(task)
    return task


@router.get("/my", response_model=list[TaskResponse])
async def my_tasks(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Task).where(Task.assignee_id == user.id).order_by(Task.priority.desc())
    )
    return result.scalars().all()
