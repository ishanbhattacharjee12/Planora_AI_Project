import os
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RequireAdmin, get_current_user
from app.config import settings
from app.database import get_db
from app.models import AuditLog, ClassificationLevel, User
from app.rag.service import save_upload
from app.schemas import AuditLogResponse, DocumentResponse
from app.services.audit_service import log_audit

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def audit_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(RequireAdmin),
):
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def upload_company_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    classification: ClassificationLevel = Form(ClassificationLevel.INTERNAL),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(RequireAdmin),
):
    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="File too large")
    doc = await save_upload(
        db,
        file_content=content,
        filename=file.filename or "document",
        title=title,
        uploaded_by_id=admin.id,
        classification=classification,
        is_company_wide=True,
        mime_type=file.content_type,
    )
    await log_audit(db, user_id=admin.id, action="upload_document", resource_type="document", resource_id=doc.id)
    return doc
