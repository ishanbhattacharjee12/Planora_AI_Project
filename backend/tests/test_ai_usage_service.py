from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services.ai_usage_service import get_analysis_token_usage


@pytest.mark.asyncio
async def test_get_analysis_token_usage_empty(db_session):
    usage = await get_analysis_token_usage(db_session, project_id=9999, version_number=1)
    assert usage["input_tokens"] == 0
    assert usage["output_tokens"] == 0
    assert usage["total_tokens"] == 0


@pytest.mark.asyncio
async def test_get_analysis_token_usage_since(db_session):
    from app.models import AIRequest

    now = datetime.now(timezone.utc)
    db_session.add(
        AIRequest(
            project_id=1,
            request_type="analysis_executive_dashboard",
            model="test-model",
            status="success",
            prompt_tokens=1200,
            completion_tokens=450,
            created_at=now,
        )
    )
    db_session.add(
        AIRequest(
            project_id=1,
            request_type="analysis_projects",
            model="test-model",
            status="success",
            prompt_tokens=800,
            completion_tokens=300,
            created_at=now + timedelta(seconds=5),
        )
    )
    await db_session.flush()

    usage = await get_analysis_token_usage(
        db_session,
        project_id=1,
        version_number=1,
        since=now - timedelta(seconds=1),
    )
    assert usage["input_tokens"] == 2000
    assert usage["output_tokens"] == 750
    assert usage["total_tokens"] == 2750
    assert usage["request_count"] == 2


@pytest.mark.asyncio
async def test_persisted_usage_selects_latest_request_per_stored_section(db_session):
    from app.models import AIRequest, AnalysisStatus, ProjectAnalysis

    now = datetime.now(timezone.utc)
    db_session.add_all([
        AIRequest(project_id=7, request_type="analysis_product_blueprint", model="test", status="success", prompt_tokens=10, completion_tokens=20, created_at=now),
        AIRequest(project_id=7, request_type="analysis_product_blueprint", model="test", status="success", prompt_tokens=100, completion_tokens=200, created_at=now + timedelta(seconds=5)),
        AIRequest(project_id=7, request_type="analysis_solution_architecture", model="test", status="success", prompt_tokens=300, completion_tokens=400, created_at=now + timedelta(seconds=10)),
        ProjectAnalysis(project_id=7, version_number=1, step="product_blueprint", payload={}, status=AnalysisStatus.DRAFT, created_at=now + timedelta(seconds=6)),
        ProjectAnalysis(project_id=7, version_number=1, step="solution_architecture", payload={}, status=AnalysisStatus.DRAFT, created_at=now + timedelta(seconds=11)),
    ])
    await db_session.flush()

    usage = await get_analysis_token_usage(db_session, project_id=7, version_number=1)
    assert usage["request_count"] == 2
    assert usage["input_tokens"] == 400
    assert usage["output_tokens"] == 600
