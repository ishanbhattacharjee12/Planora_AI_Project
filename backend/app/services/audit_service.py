from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def log_audit(
    db: AsyncSession,
    *,
    user_id: int | None,
    action: str,
    resource_type: str | None = None,
    resource_id: int | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc),
        )
    )
