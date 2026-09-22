from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AnalysisStatus,
    Project,
    ProjectAnalysis,
    ProjectMember,
    ProjectStatus,
    ProjectVersion,
    Task,
    TaskStatus,
    User,
)


async def get_project(db: AsyncSession, project_id: int) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


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

    if user.role == UserRole.EMPLOYEE or getattr(user.role, "value", None) == "employee":
        my_tasks = (await db.execute(
            select(func.count()).select_from(Task).where(
                Task.assignee_id == user.id,
                Task.status != TaskStatus.DONE,
            )
        )).scalar() or 0
        return {"my_tasks": my_tasks, "total_projects": 0, "active_projects": 0,
                "completed_projects": 0, "overdue_projects": 0, "pending_tasks": my_tasks, "overdue_tasks": 0}

    role_val = getattr(user.role, "value", str(user.role))
    if role_val == "admin":
        projects_query = select(Project)
    elif role_val == "manager":
        member_proj_ids = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
        projects_query = select(Project).where(
            or_(Project.created_by_id == user.id, Project.id.in_(member_proj_ids))
        )
    else:
        projects_query = (
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == user.id)
        )

    projects_res = await db.execute(projects_query)
    accessible_projects = projects_res.scalars().all()

    total = len(accessible_projects)
    active_statuses = {
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.APPROVED,
        ProjectStatus.REVIEW,
        "in_progress",
        "approved",
        "review",
    }
    completed_statuses = {ProjectStatus.COMPLETED, "completed"}
    overdue_statuses = {ProjectStatus.OVERDUE, "overdue"}

    active = sum(1 for p in accessible_projects if (p.status in active_statuses or getattr(p.status, "value", None) in active_statuses))
    completed = sum(1 for p in accessible_projects if (p.status in completed_statuses or getattr(p.status, "value", None) in completed_statuses))
    overdue_projects = sum(1 for p in accessible_projects if (p.status in overdue_statuses or getattr(p.status, "value", None) in overdue_statuses))

    accessible_project_ids = [p.id for p in accessible_projects]
    if accessible_project_ids:
        pending_tasks = (await db.execute(
            select(func.count()).select_from(Task).where(
                Task.project_id.in_(accessible_project_ids),
                Task.status != TaskStatus.DONE,
            )
        )).scalar() or 0

        now_utc = datetime.now(timezone.utc)
        overdue_tasks = (await db.execute(
            select(func.count()).select_from(Task).where(
                Task.project_id.in_(accessible_project_ids),
                Task.status != TaskStatus.DONE,
                Task.deadline.is_not(None),
                Task.deadline < now_utc,
            )
        )).scalar() or 0
    else:
        pending_tasks = 0
        overdue_tasks = 0

    return {
        "total_projects": total,
        "active_projects": active,
        "completed_projects": completed,
        "overdue_projects": overdue_projects,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "my_tasks": 0,
    }
