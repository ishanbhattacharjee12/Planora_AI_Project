from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AnalysisStatus,
    Project,
    ProjectAnalysis,
    ProjectMember,
    ProjectStatus,
    ProjectVersion,
    Requirement,
    Task,
    TaskDependency,
    TaskPriority,
    TaskStatus,
    Technology,
    User,
)


async def get_project(db: AsyncSession, project_id: int) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def _analysis_for_steps(
    db: AsyncSession, project: Project, steps: tuple[str, ...]
) -> ProjectAnalysis | None:
    """Return the newest current-version analysis using the preferred step order."""
    result = await db.execute(
        select(ProjectAnalysis)
        .where(
            ProjectAnalysis.project_id == project.id,
            ProjectAnalysis.version_number == project.current_version,
            ProjectAnalysis.step.in_(steps),
        )
        .order_by(ProjectAnalysis.id.desc())
    )
    by_step: dict[str, ProjectAnalysis] = {}
    for analysis in result.scalars().all():
        by_step.setdefault(analysis.step, analysis)
    return next((by_step[step] for step in steps if step in by_step), None)


async def user_can_access_project(db: AsyncSession, user: User, project_id: int) -> bool:
    if user.role.value == "admin":
        return True
    if (await get_project(db, project_id)) is None:
        return False
    project = await get_project(db, project_id)
    if project and project.created_by_id == user.id:
        return True
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    return result.scalar_one_or_none() is not None


async def approve_project_plan(db: AsyncSession, project: Project, user_id: int) -> Project:
    result = await db.execute(
        select(ProjectAnalysis).where(
            ProjectAnalysis.project_id == project.id,
            ProjectAnalysis.version_number == project.current_version,
        )
    )
    for analysis in result.scalars().all():
        analysis.status = AnalysisStatus.APPROVED

    snapshot = {
        "analyses": [
            {"step": a.step, "payload": a.payload}
            for a in (await db.execute(
                select(ProjectAnalysis).where(
                    ProjectAnalysis.project_id == project.id,
                    ProjectAnalysis.version_number == project.current_version,
                )
            )).scalars().all()
        ]
    }
    db.add(
        ProjectVersion(
            project_id=project.id,
            version_number=project.current_version,
            snapshot=snapshot,
            change_summary="Manager approved AI analysis",
            created_by_id=user_id,
        )
    )
    project.status = ProjectStatus.APPROVED
    return project


async def generate_tasks_from_analysis(db: AsyncSession, project: Project) -> list[Task]:
    analysis = await _analysis_for_steps(db, project, ("delivery_plan", "implementation_approach"))
    if not analysis:
        return []

    tasks_data = analysis.payload.get("tasks", [])
    created: list[Task] = []
    task_map: dict[str, int] = {}

    for item in tasks_data:
        priority_str = str(item.get("priority", "medium")).lower()
        try:
            priority = TaskPriority(priority_str)
        except ValueError:
            priority = TaskPriority.MEDIUM
        task = Task(
            project_id=project.id,
            task_id=item["task_id"],
            name=item["name"],
            description=item.get("description"),
            priority=priority,
            estimated_effort_days=item.get("estimated_effort_days"),
            difficulty=item.get("difficulty"),
            required_skills=item.get("required_skills"),
            acceptance_criteria="\n".join(item.get("acceptance_criteria", [])),
            version_number=project.current_version,
        )
        db.add(task)
        await db.flush()
        task_map[item["task_id"]] = task.id
        created.append(task)

    for item in tasks_data:
        task_db_id = task_map.get(item["task_id"])
        for dep_id in item.get("dependencies", []):
            dep_db_id = task_map.get(dep_id)
            if task_db_id and dep_db_id:
                db.add(TaskDependency(task_id=task_db_id, depends_on_task_id=dep_db_id))

    projects_analysis = await _analysis_for_steps(db, project, ("product_blueprint", "projects"))
    if projects_analysis:
        for item in projects_analysis.payload.get("functional", []):
            db.add(
                Requirement(
                    project_id=project.id,
                    req_id=item["req_id"],
                    req_type="functional",
                    description=item["description"],
                    priority=item.get("priority", "medium"),
                    acceptance_criteria="\n".join(item.get("acceptance_criteria", [])),
                    version_number=project.current_version,
                )
            )
        for item in projects_analysis.payload.get("non_functional", []):
            db.add(
                Requirement(
                    project_id=project.id,
                    req_id=item["req_id"],
                    req_type="non_functional",
                    description=item["description"],
                    priority=item.get("priority", "medium"),
                    acceptance_criteria="\n".join(item.get("acceptance_criteria", [])),
                    version_number=project.current_version,
                )
            )

    tech_stack: list[dict] = []
    for stack_step in ("solution_architecture", "projects", "data_structure"):
        architecture_analysis = await _analysis_for_steps(db, project, (stack_step,))
        if architecture_analysis and architecture_analysis.payload.get("stack"):
            tech_stack = architecture_analysis.payload.get("stack", [])
            break

    if tech_stack:
        for item in tech_stack:
            db.add(
                Technology(
                    project_id=project.id,
                    category=item.get("category", "general"),
                    name=item.get("name", ""),
                    rationale=item.get("rationale"),
                    alternatives={"items": []},
                    version_number=project.current_version,
                )
            )

    project.status = ProjectStatus.IN_PROGRESS
    await db.flush()
    return created


async def get_employee_workload(db: AsyncSession, employee_id: int) -> dict:
    result = await db.execute(
        select(Task).where(
            Task.assignee_id == employee_id,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW]),
        )
    )
    tasks = result.scalars().all()
    total_effort = sum(t.estimated_effort_days or 1 for t in tasks)
    user = (await db.execute(select(User).where(User.id == employee_id))).scalar_one()
    capacity = user.capacity_percent if user else 100
    workload_percent = min(100.0, round((total_effort / 20) * 100, 1))  # ~20 days = 100%
    return {
        "employee_id": employee_id,
        "full_name": user.full_name if user else "",
        "active_tasks": len(tasks),
        "total_effort_days": total_effort,
        "workload_percent": workload_percent,
        "capacity_percent": capacity,
    }


async def get_dashboard_stats(db: AsyncSession, user: User) -> dict:
    from app.models import UserRole

    if user.role == UserRole.EMPLOYEE:
        my_tasks = (await db.execute(
            select(func.count()).select_from(Task).where(
                Task.assignee_id == user.id,
                Task.status != TaskStatus.DONE,
            )
        )).scalar() or 0
        return {"my_tasks": my_tasks, "total_projects": 0, "active_projects": 0,
                "completed_projects": 0, "pending_tasks": my_tasks, "overdue_tasks": 0}

    total = (await db.execute(select(func.count()).select_from(Project))).scalar() or 0
    active = (await db.execute(
        select(func.count()).select_from(Project).where(
            Project.status.in_([ProjectStatus.IN_PROGRESS, ProjectStatus.APPROVED, ProjectStatus.REVIEW])
        )
    )).scalar() or 0
    completed = (await db.execute(
        select(func.count()).select_from(Project).where(Project.status == ProjectStatus.COMPLETED)
    )).scalar() or 0
    pending_tasks = (await db.execute(
        select(func.count()).select_from(Task).where(Task.status != TaskStatus.DONE)
    )).scalar() or 0
    overdue = (await db.execute(
        select(func.count()).select_from(Task).where(
            Task.status != TaskStatus.DONE,
            Task.deadline < datetime.now(timezone.utc),
        )
    )).scalar() or 0
    return {
        "total_projects": total,
        "active_projects": active,
        "completed_projects": completed,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue,
        "my_tasks": 0,
    }
