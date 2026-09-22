from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RequireManager
from app.database import get_db
from app.models import User
from app.schemas import (
    ProjectMemoryLogResponse,
    ProjectSimilarityRequest,
    SimilarProjectResponse,
)
from app.services.project_memory import find_similar_projects, list_project_memories


router = APIRouter(prefix="/logs", tags=["project-memory"])


@router.get("", response_model=list[ProjectMemoryLogResponse])
async def get_memory_logs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    return await list_project_memories(db, user.id)


@router.post("/similar", response_model=list[SimilarProjectResponse])
async def check_similar_projects(
    body: ProjectSimilarityRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RequireManager),
):
    return await find_similar_projects(
        db,
        owner_id=user.id,
        project_data=body.model_dump(),
    )
