"""Aggregate AI token usage for project analysis runs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AIRequest, ProjectAnalysis


def _empty_usage(project_id: int, version_number: int) -> dict:
    return {
        "project_id": project_id,
        "version_number": version_number,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "request_count": 0,
        "last_run_at": None,
    }


def _analysis_request_filter(project_id: int, since: datetime | None, until: datetime | None):
    clauses = [
        AIRequest.project_id == project_id,
        AIRequest.status == "success",
        or_(
            AIRequest.request_type.like("analysis_%"),
            AIRequest.request_type.like("agent_%"),
        ),
    ]
    if since is not None:
        clauses.append(AIRequest.created_at >= since)
    if until is not None:
        clauses.append(AIRequest.created_at <= until)
    return clauses


async def get_analysis_token_usage(
    db: AsyncSession,
    project_id: int,
    *,
    version_number: int,
    since: datetime | None = None,
) -> dict:
    """Return input/output token totals for an analysis run.

    If ``since`` is set, aggregate all successful analysis/agent requests from that
    timestamp (used while a run is in progress). Otherwise, scope to the latest
    analysis batch for the given project version.
    """
    if since is not None:
        return await _aggregate_requests(db, project_id, version_number, since=since)

    result = await db.execute(
        select(ProjectAnalysis)
        .where(
            ProjectAnalysis.project_id == project_id,
            ProjectAnalysis.version_number == version_number,
        )
        .order_by(ProjectAnalysis.step, ProjectAnalysis.id)
    )
    rows = result.scalars().all()
    if not rows:
        return _empty_usage(project_id, version_number)

    latest_by_step: dict[str, ProjectAnalysis] = {}
    for row in rows:
        latest_by_step[row.step] = row

    run_end = max(a.created_at for a in latest_by_step.values()) + timedelta(minutes=1)
    request_types = {
        request_type
        for step in latest_by_step
        for request_type in (f"analysis_{step}", f"agent_{step}")
    }
    requests_result = await db.execute(
        select(AIRequest)
        .where(
            AIRequest.project_id == project_id,
            AIRequest.status == "success",
            AIRequest.request_type.in_(request_types),
            AIRequest.created_at <= run_end,
        )
        .order_by(AIRequest.created_at.desc(), AIRequest.id.desc())
    )
    latest_request_by_step: dict[str, AIRequest] = {}
    for request in requests_result.scalars().all():
        step = request.request_type.removeprefix("analysis_").removeprefix("agent_")
        if step in latest_by_step:
            latest_request_by_step.setdefault(step, request)

    selected = list(latest_request_by_step.values())
    input_tokens = sum(request.prompt_tokens or 0 for request in selected)
    output_tokens = sum(request.completion_tokens or 0 for request in selected)
    last_run_at = max((request.created_at for request in selected), default=None)
    return {
        "project_id": project_id,
        "version_number": version_number,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "request_count": len(selected),
        "last_run_at": last_run_at.astimezone(timezone.utc).isoformat() if last_run_at else None,
    }


async def _aggregate_requests(
    db: AsyncSession,
    project_id: int,
    version_number: int,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> dict:
    clauses = _analysis_request_filter(project_id, since, until)
    result = await db.execute(
        select(
            func.coalesce(func.sum(AIRequest.prompt_tokens), 0),
            func.coalesce(func.sum(AIRequest.completion_tokens), 0),
            func.count(AIRequest.id),
            func.max(AIRequest.created_at),
        ).where(*clauses)
    )
    input_tokens, output_tokens, request_count, last_run_at = result.one()
    input_tokens = int(input_tokens or 0)
    output_tokens = int(output_tokens or 0)
    return {
        "project_id": project_id,
        "version_number": version_number,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "request_count": int(request_count or 0),
        "last_run_at": last_run_at.astimezone(timezone.utc).isoformat() if last_run_at else None,
    }
