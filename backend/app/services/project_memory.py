"""Durable project memory backed by SQL metadata and Chroma vector search."""

from __future__ import annotations

import asyncio
import hashlib
import math
import re
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Project, ProjectAnalysis, ProjectMemoryLog
from app.services.tracing import observation


COLLECTION_NAME = "project_memories_v1"
EMBEDDING_VERSION = "local-feature-hash-v1"


def _clean(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]


def _technology(value: str | None) -> str:
    return _clean(value, 100).replace("_", " ").strip().title() or "Not specified"


def _normalized_terms(value: str) -> list[str]:
    terms: list[str] = []
    aliases = {
        "application": "app",
        "applications": "app",
        "website": "web",
        "university": "student",
        "college": "student",
        "learner": "student",
        "gpa": "academic-grade",
        "cgpa": "academic-grade",
        "sgpa": "academic-grade",
        "grade": "academic-grade",
        "grades": "academic-grade",
        "inventory": "inventory",
        "stock": "inventory",
        "warehouse": "inventory",
        "shipment": "delivery",
        "shopping": "ecommerce",
        "cart": "ecommerce",
        "checkout": "ecommerce",
        "payment": "ecommerce",
        "payments": "ecommerce",
        "vacation": "leave",
        "absence": "leave",
    }
    for word in re.findall(r"[a-z0-9]+", value.lower()):
        if len(word) <= 2 or word in {
            "the", "and", "for", "with", "project", "build", "that", "idea", "summary",
            "architecture", "frontend", "backend", "database", "specified", "not", "app",
        }:
            continue
        word = aliases.get(word, word)
        if word.startswith("calculat"):
            word = "calculate"
        elif word == "grading":
            word = "academic-grade"
        elif word.endswith("s") and len(word) > 4:
            word = word[:-1]
        terms.append(word)
    return terms


def _local_embedding(value: str, dimensions: int = 384) -> list[float]:
    """Fast, deterministic topical embedding for offline duplicate detection."""
    terms = _normalized_terms(value)
    features = terms + [f"{a}:{b}" for a, b in zip(terms, terms[1:])]
    vector = [0.0] * dimensions
    for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "little") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign
    magnitude = math.sqrt(sum(component * component for component in vector)) or 1.0
    return [component / magnitude for component in vector]


def build_project_memory(
    *,
    name: str,
    idea: str,
    description: str | None = None,
    business_objective: str | None = None,
    project_type: str | None = None,
    primary_users: str | None = None,
    frontend_technology: str | None = None,
    backend_technology: str | None = None,
    database_technology: str | None = None,
    analysis_summary: str | None = None,
) -> dict[str, str]:
    clean_idea = _clean(idea, 1600)
    summary_source = analysis_summary or description or business_objective or clean_idea
    summary = _clean(summary_source, 650)
    snippet = _clean(clean_idea, 260)
    architecture = (
        f"Frontend: {_technology(frontend_technology)} · "
        f"Backend: {_technology(backend_technology)} · "
        f"Database: {_technology(database_technology)}"
    )
    semantic_parts = [
        f"Project: {_clean(name, 200)}",
        f"Idea: {clean_idea}",
        f"Summary: {summary}",
        f"Architecture: {architecture}",
    ]
    if business_objective:
        semantic_parts.append(f"Business objective: {_clean(business_objective, 500)}")
    if project_type:
        semantic_parts.append(f"Project type: {_clean(project_type, 120)}")
    if primary_users:
        semantic_parts.append(f"Primary users: {_clean(primary_users, 300)}")
    return {
        "snippet": snippet,
        "summary": summary,
        "architecture": architecture,
        "semantic_summary": "\n".join(semantic_parts),
    }


def _analysis_summary(analyses: Iterable[ProjectAnalysis] | None) -> str | None:
    if not analyses:
        return None
    materialized = list(analyses)
    for preferred_step in ("product_blueprint", "executive_dashboard"):
        for analysis in materialized:
            if analysis.step != preferred_step:
                continue
            overview = analysis.payload.get("overview") if analysis.payload else None
            if overview:
                return _clean(overview, 650)
    return None


@lru_cache(maxsize=1)
def _collection():
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=settings.chroma_persist_path,
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )


def _index_record(log: ProjectMemoryLog, project_name: str) -> None:
    collection = _collection()
    collection.upsert(
        ids=[log.chroma_id],
        documents=[log.semantic_summary],
        embeddings=[_local_embedding(log.semantic_summary)],
        metadatas=[{
            "project_id": log.project_id,
            "owner_id": log.owner_id,
            "project_name": project_name,
            "architecture": log.architecture,
            "embedding_version": EMBEDDING_VERSION,
        }],
    )


def _delete_index_record(chroma_id: str) -> None:
    """Remove one project from the semantic index."""
    _collection().delete(ids=[chroma_id])


async def delete_project_memory_index(chroma_id: str | None) -> None:
    """Best-effort vector cleanup used after a project is permanently deleted."""
    if not chroma_id or not settings.project_memory_enabled:
        return
    try:
        await asyncio.to_thread(_delete_index_record, chroma_id)
    except Exception:
        # Database deletion remains authoritative if the optional vector store is unavailable.
        return


async def upsert_project_memory(
    db: AsyncSession,
    project: Project,
    analyses: Iterable[ProjectAnalysis] | None = None,
) -> ProjectMemoryLog:
    content = build_project_memory(
        name=project.name,
        idea=project.idea,
        description=project.description,
        business_objective=project.business_objective,
        project_type=project.project_type,
        primary_users=project.primary_users,
        frontend_technology=project.frontend_technology,
        backend_technology=project.backend_technology,
        database_technology=project.database_technology,
        analysis_summary=_analysis_summary(analyses),
    )
    result = await db.execute(
        select(ProjectMemoryLog).where(ProjectMemoryLog.project_id == project.id)
    )
    log = result.scalar_one_or_none()
    if log is None:
        log = ProjectMemoryLog(
            project_id=project.id,
            owner_id=project.created_by_id,
            chroma_id=f"project-{project.id}",
            **content,
        )
        db.add(log)
    else:
        for key, value in content.items():
            setattr(log, key, value)
        log.owner_id = project.created_by_id
        log.index_status = "pending"
        log.index_error = None
    await db.flush()

    if not settings.project_memory_enabled:
        return log

    try:
        with observation(
            "index-project-memory",
            as_type="embedding",
            input={"project_id": project.id, "document_chars": len(log.semantic_summary)},
            metadata={"store": "chroma", "collection": COLLECTION_NAME,
                      "embedding_version": EMBEDDING_VERSION},
        ) as span:
            await asyncio.to_thread(_index_record, log, project.name)
            if span is not None:
                span.update(output={"indexed": True, "chroma_id": log.chroma_id})
        log.index_status = "indexed"
        log.index_error = None
    except Exception as exc:  # Keep project creation available if vector storage is temporarily down.
        log.index_status = "error"
        log.index_error = _clean(exc, 500)
    await db.flush()
    return log


def _query_chroma(semantic_summary: str, owner_id: int, limit: int) -> list[tuple[int, float]]:
    collection = _collection()
    if collection.count() == 0:
        return []
    result = collection.query(
        query_embeddings=[_local_embedding(semantic_summary)],
        n_results=min(limit, collection.count()),
        where={"owner_id": owner_id},
        include=["distances", "metadatas"],
    )
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    matches: list[tuple[int, float]] = []
    for metadata, distance in zip(metadatas, distances):
        if not metadata or metadata.get("project_id") is None:
            continue
        similarity = max(0.0, min(1.0, 1.0 - float(distance)))
        matches.append((int(metadata["project_id"]), similarity))
    return matches


def _keyword_similarity(left: str, right: str) -> float:
    a, b = set(_normalized_terms(left)), set(_normalized_terms(right))
    return len(a & b) / len(a | b) if a and b else 0.0


async def find_similar_projects(
    db: AsyncSession,
    *,
    owner_id: int,
    project_data: dict[str, Any],
    limit: int = 3,
) -> list[dict[str, Any]]:
    content = build_project_memory(**project_data)
    vector_matches: list[tuple[int, float]] = []
    if settings.project_memory_enabled:
        try:
            with observation(
                "search-project-memory",
                as_type="retriever",
                input={"owner_id": owner_id, "query_chars": len(content["semantic_summary"])},
                metadata={"store": "chroma", "limit": limit},
            ) as span:
                vector_matches = await asyncio.to_thread(
                    _query_chroma, content["semantic_summary"], owner_id, limit
                )
                if span is not None:
                    span.update(output={"candidate_count": len(vector_matches)})
        except Exception:
            vector_matches = []

    result = await db.execute(
        select(ProjectMemoryLog, Project)
        .join(Project, Project.id == ProjectMemoryLog.project_id)
        .where(ProjectMemoryLog.owner_id == owner_id)
    )
    rows = result.all()
    similarity_by_id = dict(vector_matches)
    if not similarity_by_id:
        similarity_by_id = {
            log.project_id: _keyword_similarity(content["semantic_summary"], log.semantic_summary)
            for log, _project in rows
        }

    matches = []
    for log, project in rows:
        similarity = similarity_by_id.get(project.id, 0.0)
        if similarity < settings.project_similarity_threshold:
            continue
        matches.append({
            "project_id": project.id,
            "project_name": project.name,
            "snippet": log.snippet,
            "summary": log.summary,
            "architecture": log.architecture,
            "similarity": round(similarity, 4),
            "created_at": log.created_at,
        })
    matches.sort(key=lambda item: item["similarity"], reverse=True)
    return matches[:limit]


async def list_project_memories(db: AsyncSession, owner_id: int) -> list[dict[str, Any]]:
    result = await db.execute(
        select(ProjectMemoryLog, Project)
        .join(Project, Project.id == ProjectMemoryLog.project_id)
        .where(ProjectMemoryLog.owner_id == owner_id)
        .order_by(ProjectMemoryLog.updated_at.desc())
    )
    return [
        {
            "id": log.id,
            "project_id": log.project_id,
            "project_name": project.name,
            "snippet": log.snippet,
            "summary": log.summary,
            "architecture": log.architecture,
            "semantic_summary": log.semantic_summary,
            "index_status": log.index_status,
            "created_at": log.created_at,
            "updated_at": log.updated_at,
        }
        for log, project in result.all()
    ]
