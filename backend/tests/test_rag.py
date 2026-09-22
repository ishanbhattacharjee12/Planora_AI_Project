import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Document, DocumentChunk, User
from app.rag.service import _cosine_similarity, search_chunks


@pytest.mark.asyncio
async def test_cosine_similarity_calculation():
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    vec_c = [0.0, 1.0, 0.0]
    assert _cosine_similarity(vec_a, vec_b) == pytest.approx(1.0)
    assert _cosine_similarity(vec_a, vec_c) == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_search_chunks_ranking_and_limit(db_session: AsyncSession, manager_user: User):
    doc = Document(
        title="Architecture Specs",
        filename="specs.pdf",
        file_path="/tmp/specs.pdf",
        uploaded_by_id=manager_user.id,
        project_id=1,
    )
    db_session.add(doc)
    await db_session.flush()

    # Add 5 chunks with distinct embeddings
    for idx in range(5):
        db_session.add(
            DocumentChunk(
                document_id=doc.id,
                project_id=1,
                chunk_index=idx,
                content=f"Content chunk {idx}",
                embedding=[0.1 * (idx + 1)] * 384,
                metadata_json={"chunk": idx},
            )
        )
    await db_session.flush()

    # Search with limit=3
    results = await search_chunks(db_session, "Architecture query", authorized_project_ids=[1], limit=3)
    assert len(results) == 3
    assert all(isinstance(r, DocumentChunk) for r in results)


@pytest.mark.asyncio
async def test_search_chunks_authorization_filtering(db_session: AsyncSession, manager_user: User):
    doc_proj1 = Document(
        title="Project 1 Specs",
        filename="p1.pdf",
        file_path="/tmp/p1.pdf",
        uploaded_by_id=manager_user.id,
        project_id=1,
    )
    doc_proj2 = Document(
        title="Project 2 Specs",
        filename="p2.pdf",
        file_path="/tmp/p2.pdf",
        uploaded_by_id=manager_user.id,
        project_id=2,
    )
    doc_global = Document(
        title="Global Standards",
        filename="global.pdf",
        file_path="/tmp/global.pdf",
        uploaded_by_id=manager_user.id,
        project_id=None,
    )
    db_session.add_all([doc_proj1, doc_proj2, doc_global])
    await db_session.flush()

    db_session.add(
        DocumentChunk(
            document_id=doc_proj1.id,
            project_id=1,
            chunk_index=0,
            content="Project 1 authorized content",
            embedding=[0.5] * 384,
        )
    )
    db_session.add(
        DocumentChunk(
            document_id=doc_proj2.id,
            project_id=2,
            chunk_index=0,
            content="Project 2 unauthorized content",
            embedding=[0.5] * 384,
        )
    )
    db_session.add(
        DocumentChunk(
            document_id=doc_global.id,
            project_id=None,
            chunk_index=0,
            content="Global company-wide content",
            embedding=[0.5] * 384,
        )
    )
    await db_session.flush()

    # User is only authorized for project 1
    results = await search_chunks(db_session, "query", authorized_project_ids=[1], limit=10)
    contents = [r.content for r in results]
    assert "Project 1 authorized content" in contents
    assert "Global company-wide content" in contents
    assert "Project 2 unauthorized content" not in contents


@pytest.mark.asyncio
async def test_search_chunks_with_postgresql_url_setting(db_session: AsyncSession, manager_user: User, monkeypatch):
    """Ensure that when database_url is set to PostgreSQL, search_chunks still uses resilient in-memory cosine ranking."""
    monkeypatch.setattr(settings, "database_url", "postgresql+asyncpg://user:pass@render-pg.com/db")

    doc = Document(
        title="Security Specs",
        filename="sec.pdf",
        file_path="/tmp/sec.pdf",
        uploaded_by_id=manager_user.id,
        project_id=10,
    )
    db_session.add(doc)
    await db_session.flush()

    db_session.add(
        DocumentChunk(
            document_id=doc.id,
            project_id=10,
            chunk_index=0,
            content="Security compliance checklist",
            embedding=[0.2] * 384,
        )
    )
    await db_session.flush()

    # Should execute successfully without throwing undefined operator error
    results = await search_chunks(db_session, "Security checklist", authorized_project_ids=[10], limit=3)
    assert len(results) == 1
    assert results[0].content == "Security compliance checklist"
