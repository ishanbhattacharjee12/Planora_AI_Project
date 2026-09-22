import math
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import ai_gateway
from app.config import settings
from app.models import Document, DocumentChunk, ProjectMember
from app.services.tracing import observation


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i : i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks


def extract_text(file_path: str, mime_type: str | None) -> str:
    from pathlib import Path
    from pypdf import PdfReader

    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf" or mime_type == "application/pdf":
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


async def get_authorized_project_ids(db: AsyncSession, user_id: int, is_admin: bool) -> list[int]:
    if is_admin:
        from app.models import Project
        result = await db.execute(select(Project.id))
        return [row[0] for row in result.all()]
    result = await db.execute(select(ProjectMember.project_id).where(ProjectMember.user_id == user_id))
    return [row[0] for row in result.all()]


async def save_upload(
    db: AsyncSession,
    *,
    file_content: bytes,
    filename: str,
    title: str,
    uploaded_by_id: int,
    project_id: int | None = None,
    department_id: int | None = None,
    classification=None,
    is_company_wide: bool = False,
    mime_type: str | None = None,
) -> Document:
    import os
    import uuid

    os.makedirs(settings.upload_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(settings.upload_dir, unique_name)
    with open(file_path, "wb") as f:
        f.write(file_content)

    doc = Document(
        title=title,
        filename=filename,
        file_path=file_path,
        mime_type=mime_type,
        project_id=project_id,
        department_id=department_id,
        classification=classification,
        uploaded_by_id=uploaded_by_id,
        is_company_wide=is_company_wide,
    )
    db.add(doc)
    await db.flush()

    text = extract_text(file_path, mime_type)
    chunks = chunk_text(text)
    if chunks:
        embeddings = await ai_gateway.embed(chunks)
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    project_id=project_id,
                    chunk_index=idx,
                    content=chunk,
                    embedding=embedding,
                    metadata_json={"title": title, "filename": filename},
                )
            )
    await db.flush()
    return doc


async def search_chunks(
    db: AsyncSession,
    query: str,
    authorized_project_ids: list[int],
    limit: int = 5,
) -> list[DocumentChunk]:
    with observation(
        "retrieve-document-context", as_type="retriever",
        input={"query_chars": len(query), "authorized_project_count": len(authorized_project_ids)},
        metadata={"limit": limit, "index": "pgvector" if "postgresql" in settings.database_url else "sqlite"},
    ) as retrieval:
        chunks = await _search_chunks(db, query, authorized_project_ids, limit)
        if retrieval is not None:
            retrieval.update(output={"chunk_count": len(chunks), "document_ids": sorted({c.document_id for c in chunks})})
        return chunks


async def _search_chunks(
    db: AsyncSession, query: str, authorized_project_ids: list[int], limit: int,
) -> list[DocumentChunk]:
    query_embedding = (await ai_gateway.embed([query]))[0]

    if "postgresql" in settings.database_url:
        from sqlalchemy import text as sql_text
        ids_clause = ",".join(str(i) for i in authorized_project_ids) if authorized_project_ids else "0"
        sql = sql_text(f"""
            SELECT id, document_id, project_id, chunk_index, content, metadata_json
            FROM document_chunks
            WHERE project_id IN ({ids_clause}) OR project_id IS NULL
            ORDER BY embedding <=> :embedding
            LIMIT :limit
        """)
        result = await db.execute(sql, {"embedding": str(query_embedding), "limit": limit})
        rows = result.fetchall()
        return [
            DocumentChunk(
                id=row.id, document_id=row.document_id, project_id=row.project_id,
                chunk_index=row.chunk_index, content=row.content, metadata_json=row.metadata_json,
            )
            for row in rows
        ]

    # SQLite fallback: brute-force cosine similarity
    result = await db.execute(select(DocumentChunk))
    all_chunks = result.scalars().all()
    scored = []
    for chunk in all_chunks:
        if chunk.project_id and chunk.project_id not in authorized_project_ids:
            continue
        if chunk.embedding:
            score = _cosine_similarity(query_embedding, list(chunk.embedding))
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]
