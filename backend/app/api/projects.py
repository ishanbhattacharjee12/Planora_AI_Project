from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import AIGatewayError, SensitiveDataError
from app.auth.dependencies import RequireManager, get_current_user
from app.config import settings
from app.database import get_db
from app.models import (
    AIRequest,
    AIResponse,
    AnalysisStatus,
    AssistantMessage,
    AuditLog,
    Document,
    DocumentChunk,
    OrchestrationRun,
    Project,
    ProjectAnalysis,
    ProjectMember,
    ProjectMemoryLog,
    ProjectStatus,
    ProjectVersion,
    Requirement,
    Task,
    TaskDependency,
    Technology,
    User,
)
from app.orchestration.agents.graph import run_agent_orchestration
from app.orchestration.workflow import run_analysis_workflow
from app.rag.service import get_authorized_project_ids, search_chunks
from app.schemas import (
    AnalysisStepResponse,
    AnalysisTokenUsageResponse,
    AnalysisUpdate,
    AnalyzeProjectResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectVersionResponse,
    VersionDiffResponse,
)
from app.services.ai_usage_service import get_analysis_token_usage
from app.services.audit_service import log_audit
from app.services.analysis_pdf import analysis_pdf_filename, build_analysis_pdf
from app.services.project_service import (
    approve_project_plan,
    generate_tasks_from_analysis,
    get_project,
    user_can_access_project,
)
from app.services.project_memory import delete_project_memory_index, upsert_project_memory
from app.services.tech_stack import compose_known_technologies
from app.services.tracing import attributes, observation

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    data = body.model_dump()
    if not data.get("known_technologies"):
        data["known_technologies"] = compose_known_technologies(
            data.get("frontend_technology"),
            data.get("backend_technology"),
            data.get("database_technology"),
        )
    project = Project(**data, created_by_id=user.id, status=ProjectStatus.DRAFT)
    db.add(project)
    await db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=user.id, role="owner"))
    await log_audit(
        db, user_id=user.id, action="create_project",
        resource_type="project", resource_id=project.id,
        ip_address=request.client.host if request.client else None,
    )
    await upsert_project_memory(db, project)
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role.value == "admin":
        result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    elif user.role.value == "manager":
        result = await db.execute(
            select(Project).where(Project.created_by_id == user.id).order_by(Project.created_at.desc())
        )
    else:
        result = await db.execute(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == user.id)
            .order_by(Project.created_at.desc())
        )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_detail(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await user_can_access_project(db, user, project_id):
        raise HTTPException(status_code=403, detail="Access denied")
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not await user_can_access_project(db, user, project_id):
        raise HTTPException(status_code=403, detail="Access denied")
    updates = body.model_dump(exclude_unset=True)
    stack_fields = {"frontend_technology", "backend_technology", "database_technology"}
    if stack_fields & updates.keys() and "known_technologies" not in updates:
        updates["known_technologies"] = compose_known_technologies(
            updates.get("frontend_technology", project.frontend_technology),
            updates.get("backend_technology", project.backend_technology),
            updates.get("database_technology", project.database_technology),
        )
    for key, value in updates.items():
        setattr(project, key, value)
    await db.flush()
    await db.refresh(project)
    await upsert_project_memory(db, project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_permanently(
    project_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    """Permanently remove a project and every database record owned by it."""
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role.value != "admin" and project.created_by_id != user.id:
        raise HTTPException(status_code=403, detail="Only the project owner can delete this project")

    memory = (
        await db.execute(
            select(ProjectMemoryLog).where(ProjectMemoryLog.project_id == project_id)
        )
    ).scalar_one_or_none()
    chroma_id = memory.chroma_id if memory else None

    task_ids = list(
        (await db.execute(select(Task.id).where(Task.project_id == project_id))).scalars()
    )
    if task_ids:
        await db.execute(
            delete(TaskDependency).where(
                or_(
                    TaskDependency.task_id.in_(task_ids),
                    TaskDependency.depends_on_task_id.in_(task_ids),
                )
            )
        )
    await db.execute(delete(Task).where(Task.project_id == project_id))

    document_ids = list(
        (await db.execute(select(Document.id).where(Document.project_id == project_id))).scalars()
    )
    chunk_filters = [DocumentChunk.project_id == project_id]
    if document_ids:
        chunk_filters.append(DocumentChunk.document_id.in_(document_ids))
    await db.execute(delete(DocumentChunk).where(or_(*chunk_filters)))
    await db.execute(delete(Document).where(Document.project_id == project_id))

    request_ids = list(
        (await db.execute(select(AIRequest.id).where(AIRequest.project_id == project_id))).scalars()
    )
    if request_ids:
        await db.execute(delete(AIResponse).where(AIResponse.request_id.in_(request_ids)))
    await db.execute(delete(AIRequest).where(AIRequest.project_id == project_id))

    for model in (
        AssistantMessage,
        OrchestrationRun,
        ProjectMemoryLog,
        ProjectAnalysis,
        ProjectVersion,
        Requirement,
        Technology,
        ProjectMember,
    ):
        await db.execute(delete(model).where(model.project_id == project_id))

    # Remove historical project events, then retain one non-relational deletion audit.
    await db.execute(
        delete(AuditLog).where(
            AuditLog.resource_type == "project",
            AuditLog.resource_id == project_id,
        )
    )
    project_name = project.name
    await db.execute(delete(Project).where(Project.id == project_id))
    await log_audit(
        db,
        user_id=user.id,
        action="delete_project",
        resource_type="project",
        metadata={"deleted_project_id": project_id, "deleted_project_name": project_name},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await delete_project_memory_index(chroma_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/analyze", response_model=AnalyzeProjectResponse)
async def analyze_project(
    project_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        with observation(
            "analyze-project", as_type="chain",
            input={"project_id": project_id, "idea_chars": len(project.idea)},
            metadata={"version": project.current_version, "mode": settings.orchestration_mode,
                      "classification": project.classification.value},
        ) as trace:
            with attributes(user_id=user.id, session_id=f"project-{project_id}", tags=["analysis"]):
                authorized = await get_authorized_project_ids(db, user.id, user.role.value == "admin")
                rag_context = ""
                if project_id in authorized:
                    chunks = await search_chunks(db, project.idea, authorized, limit=3)
                    rag_context = "\n".join(c.content for c in chunks)

                if settings.orchestration_mode == "agents":
                    project.status = ProjectStatus.ANALYZING
                    await db.execute(
                        delete(ProjectAnalysis).where(
                            ProjectAnalysis.project_id == project.id,
                            ProjectAnalysis.version_number == project.current_version,
                        )
                    )
                    await db.commit()
                    try:
                        results_dict = await run_agent_orchestration(db, project, user.id, rag_context)
                    except Exception:
                        await db.rollback()
                        project.status = ProjectStatus.DRAFT
                        await db.commit()
                        raise
                    analyses = []
                    for step_name, payload in results_dict.items():
                        analysis = ProjectAnalysis(
                            project_id=project.id,
                            version_number=project.current_version,
                            step=step_name,
                            payload=payload,
                            confidence=payload.get("confidence"),
                            status=AnalysisStatus.DRAFT,
                        )
                        db.add(analysis)
                        analyses.append(analysis)
                    project.status = ProjectStatus.REVIEW
                    await db.flush()
                    await db.commit()
                else:
                    analyses = await run_analysis_workflow(db, project, user.id, rag_context)
                if trace is not None:
                    trace.update(output={"section_count": len(analyses), "status": project.status.value})
    except SensitiveDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValidationError as exc:
        first_error = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(part) for part in first_error.get("loc", ()))
        message = first_error.get("msg", "invalid value")
        detail = (
            "AI returned data that did not match the expected format. Try again."
            if not location
            else f"AI returned data that did not match the expected format ({location}: {message}). Try again."
        )
        raise HTTPException(status_code=502, detail=detail) from exc
    except AIGatewayError as exc:
        message = str(exc)
        message_lower = message.lower()
        if "not configured" in message_lower:
            detail = "Gemini API key is not configured. Set GEMINI_API_KEY in environment or backend/.env."
        elif "401" in message or "403" in message or "unauthorized" in message_lower or "permission_denied" in message_lower or "api_key_invalid" in message_lower:
            detail = "Gemini rejected the configured API key. Please check your GEMINI_API_KEY."
        elif "404" in message or "not found" in message_lower or "not available" in message_lower:
            detail = f"Configured Gemini model is not available: {message}"
        elif "429" in message or "rate_limit" in message_lower or "resource_exhausted" in message_lower:
            detail = "Gemini rate limit reached. Wait a minute and try again."
        elif "json_validate_failed" in message.lower() or "failed to validate json" in message.lower():
            detail = "AI could not produce valid structured output. Please try again."
        elif "413" in message or "too large" in message.lower():
            detail = (
                "AI request exceeded provider token limits. "
                "Reduce project text or lower MAX_AI_TOKENS_PER_REQUEST in backend/.env."
            )
        elif "connection error" in message_lower or "timed out" in message_lower:
            detail = "Gemini could not be reached after several retries. Check network access, then try again."
        else:
            detail = f"Gemini error: {message}"
        raise HTTPException(status_code=502, detail=detail) from exc

    await log_audit(
        db, user_id=user.id, action="generate_ai_analysis",
        resource_type="project", resource_id=project.id,
        ip_address=request.client.host if request.client else None,
    )
    await upsert_project_memory(db, project, analyses)
    usage = await get_analysis_token_usage(
        db, project.id, version_number=project.current_version
    )
    return AnalyzeProjectResponse(steps=analyses, token_usage=usage)


@router.get("/{project_id}/analysis/usage", response_model=AnalysisTokenUsageResponse)
async def get_analysis_usage(
    project_id: int,
    since: datetime | None = Query(None, description="ISO timestamp for in-progress run totals"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await user_can_access_project(db, user, project_id):
        raise HTTPException(status_code=403, detail="Access denied")
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    usage = await get_analysis_token_usage(
        db,
        project_id,
        version_number=project.current_version,
        since=since,
    )
    return usage


@router.get("/{project_id}/analysis", response_model=list[AnalysisStepResponse])
async def get_analysis(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await user_can_access_project(db, user, project_id):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(ProjectAnalysis)
        .where(ProjectAnalysis.project_id == project_id)
        .order_by(ProjectAnalysis.id)
    )
    return result.scalars().all()


@router.get("/{project_id}/analysis/pdf")
async def download_analysis_pdf(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await user_can_access_project(db, user, project_id):
        raise HTTPException(status_code=403, detail="Access denied")

    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(ProjectAnalysis)
        .where(
            ProjectAnalysis.project_id == project_id,
            ProjectAnalysis.version_number == project.current_version,
        )
        .order_by(ProjectAnalysis.id)
    )
    analyses = result.scalars().all()
    if not analyses:
        raise HTTPException(status_code=404, detail="No analysis available to export")

    pdf_bytes = build_analysis_pdf(project, analyses)
    filename = analysis_pdf_filename(project)
    await log_audit(
        db,
        user_id=user.id,
        action="export_analysis_pdf",
        resource_type="project",
        resource_id=project.id,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{project_id}/analysis", response_model=AnalysisStepResponse)
async def update_analysis_step(
    project_id: int,
    body: AnalysisUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    result = await db.execute(
        select(ProjectAnalysis).where(
            ProjectAnalysis.project_id == project_id,
            ProjectAnalysis.step == body.step,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis step not found")
    analysis.payload = body.payload
    analysis.status = AnalysisStatus.REVIEWED
    await db.flush()
    return analysis


@router.post("/{project_id}/approve", response_model=ProjectResponse)
async def approve_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await approve_project_plan(db, project, user.id)
    await log_audit(db, user_id=user.id, action="approve_project", resource_type="project", resource_id=project.id)
    return project


@router.post("/{project_id}/generate-tasks")
async def generate_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status != ProjectStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Project must be approved first")
    tasks = await generate_tasks_from_analysis(db, project)
    await log_audit(db, user_id=user.id, action="generate_tasks", resource_type="project", resource_id=project.id)
    return {"created": len(tasks), "task_ids": [t.id for t in tasks]}


@router.get("/{project_id}/versions", response_model=list[ProjectVersionResponse])
async def list_versions(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProjectVersion)
        .where(ProjectVersion.project_id == project_id)
        .order_by(ProjectVersion.version_number.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}/versions/diff", response_model=VersionDiffResponse)
async def version_diff(
    project_id: int,
    version_a: int,
    version_b: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    va = (await db.execute(
        select(ProjectVersion).where(ProjectVersion.project_id == project_id, ProjectVersion.version_number == version_a)
    )).scalar_one_or_none()
    vb = (await db.execute(
        select(ProjectVersion).where(ProjectVersion.project_id == project_id, ProjectVersion.version_number == version_b)
    )).scalar_one_or_none()
    if not va or not vb:
        raise HTTPException(status_code=404, detail="Version not found")
    changes = {"from": va.snapshot, "to": vb.snapshot}
    return VersionDiffResponse(version_a=version_a, version_b=version_b, changes=changes)
