from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from langfuse import Langfuse
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.ai.gateway import AIGateway
from app.models import ClassificationLevel
from app.services import tracing


@pytest.mark.asyncio
async def test_ai_trace_records_usage_without_confidential_content(monkeypatch, db_session):
    exporter = InMemorySpanExporter()
    client = Langfuse(
        public_key="pk-test", secret_key="sk-test", base_url="https://example.invalid",
        environment="test", span_exporter=exporter,
    )
    monkeypatch.setattr(tracing, "_client", lambda: client)

    gateway = AIGateway()
    gateway.client.chat.completions.create = AsyncMock(return_value=SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="private model answer"))],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=8),
    ))

    with tracing.observation("analyze-project", input={"project_id": 42}) as root:
        with tracing.attributes(user_id=7, session_id="project-42", tags=["analysis"]):
            result = await gateway.complete(
                db_session,
                messages=[{"role": "user", "content": "confidential project idea"}],
                request_type="analysis_projects",
                user_id=7,
                project_id=42,
                classification=ClassificationLevel.INTERNAL,
            )
            root.update(output={"completed": True})

    assert result == "private model answer"
    client.flush()
    spans = exporter.get_finished_spans()
    assert {span.name for span in spans} >= {"analyze-project", "generate-response"}
    generation = next(span for span in spans if span.name == "generate-response")
    assert generation.parent.span_id == next(span for span in spans if span.name == "analyze-project").context.span_id
    rendered = str([dict(span.attributes) for span in spans])
    assert "confidential project idea" not in rendered
    assert "private model answer" not in rendered
    assert "12" in rendered and "8" in rendered
