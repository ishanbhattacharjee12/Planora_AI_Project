from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import RequireManager, get_current_user
from app.database import get_db
from app.models import EmployeeSkill, Skill, Task, User, UserRole
from app.schemas import EmployeeRecommendation, EmployeeResponse, EmployeeSkillResponse, SkillGapResponse, WorkloadResponse
from app.services.matching_service import (
    compute_match_score,
    find_skill_gaps,
    recommendation_label,
    skill_match_score,
    availability_score,
)
from app.services.project_service import get_employee_workload
from app.ai.gateway import ai_gateway

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeResponse])
async def list_employees(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    result = await db.execute(
        select(User)
        .where(User.role == UserRole.EMPLOYEE, User.is_active == True)
        .options(selectinload(User.employee_skills).selectinload(EmployeeSkill.skill))
    )
    employees = []
    for emp in result.scalars().all():
        skills = [
            EmployeeSkillResponse(
                skill_id=es.skill_id,
                skill_name=es.skill.name if es.skill else "",
                level=es.level,
                years_experience=es.years_experience,
            )
            for es in emp.employee_skills
        ]
        emp_data = EmployeeResponse.model_validate(emp)
        emp_data.skills = skills
        employees.append(emp_data)
    return employees


@router.get("/{employee_id}/skills")
async def get_employee_skills(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    result = await db.execute(
        select(EmployeeSkill)
        .where(EmployeeSkill.user_id == employee_id)
        .options(selectinload(EmployeeSkill.skill))
    )
    return [
        {
            "skill_id": es.skill_id,
            "skill_name": es.skill.name if es.skill else "",
            "level": es.level.value,
            "years_experience": es.years_experience,
            "certifications": es.certifications,
            "manager_rating": es.manager_rating,
        }
        for es in result.scalars().all()
    ]


@router.get("/{employee_id}/workload", response_model=WorkloadResponse)
async def get_workload(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    data = await get_employee_workload(db, employee_id)
    return WorkloadResponse(**data)


@router.get("/{employee_id}/skill-gaps", response_model=list[SkillGapResponse])
async def skill_gaps(
    employee_id: int,
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    from app.models import ProjectAnalysis

    skills_result = await db.execute(
        select(EmployeeSkill)
        .where(EmployeeSkill.user_id == employee_id)
        .options(selectinload(EmployeeSkill.skill))
    )
    emp_skills = {es.skill.name: es.level.value for es in skills_result.scalars().all() if es.skill}

    required: dict[str, str] = {}
    for step in ("team_operations", "staffing", "resources"):
        analysis = (await db.execute(
            select(ProjectAnalysis)
            .where(
                ProjectAnalysis.project_id == project_id,
                ProjectAnalysis.step == step,
            )
            .order_by(ProjectAnalysis.version_number.desc(), ProjectAnalysis.id.desc())
            .limit(1)
        )).scalar_one_or_none()
        if not analysis:
            continue
        if step == "resources":
            required = {
                s["skill"]: s.get("required_level") or s.get("proficiency", "intermediate")
                for s in analysis.payload.get("skill_matrix", [])
            }
        else:
            required = {
                s["skill"]: s["required_level"]
                for s in analysis.payload.get("required_skills", [])
            }
        if required:
            break

    if not required:
        return []
    gaps = find_skill_gaps(required, emp_skills)
    return [
        SkillGapResponse(
            skill_name=g["skill"],
            required_level=g["required_level"],
            current_level=g["current_level"],
            gap=True,
        )
        for g in gaps
    ]


@router.get("/tasks/{task_id}/recommendations", response_model=list[EmployeeRecommendation])
async def task_recommendations(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    task = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    required = task.required_skills or {}
    employees = (await db.execute(
        select(User).where(User.role == UserRole.EMPLOYEE, User.is_active == True)
        .options(selectinload(User.employee_skills).selectinload(EmployeeSkill.skill))
    )).scalars().all()

    recommendations = []
    for emp in employees:
        emp_skills = {es.skill.name: es.level.value for es in emp.employee_skills if es.skill}
        sm = skill_match_score(required, emp_skills)
        workload = await get_employee_workload(db, emp.id)
        avail = availability_score(workload["workload_percent"], emp.capacity_percent)
        score = compute_match_score(sm, sm * 0.9, avail)
        gaps = find_skill_gaps(required, emp_skills)
        recommendations.append(
            EmployeeRecommendation(
                employee_id=emp.id,
                full_name=emp.full_name,
                skill_match_percent=sm,
                workload_percent=workload["workload_percent"],
                recommendation=recommendation_label(score, workload["workload_percent"]),
                skill_gaps=gaps,
            )
        )

    recommendations.sort(key=lambda r: (-r.skill_match_percent, r.workload_percent))

    # Add AI narrative for top candidate
    if recommendations and recommendations[0].skill_match_percent > 50:
        try:
            narrative = await ai_gateway.complete(
                db,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Task: {task.name}. Required skills: {required}. "
                        f"Top candidate: {recommendations[0].full_name}, "
                        f"match {recommendations[0].skill_match_percent}%, "
                        f"workload {recommendations[0].workload_percent}%. "
                        "Give a 2-sentence assignment recommendation."
                    ),
                }],
                request_type="matching_narrative",
                user_id=user.id,
                project_id=task.project_id,
            )
            recommendations[0].narrative = narrative
        except Exception:
            pass

    return recommendations
