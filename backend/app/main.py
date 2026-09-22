from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import admin, auth, dashboard, documents, employees, logs, projects, tasks
from app.config import settings
from app.database import Base, engine
from app.db_migrations import sync_missing_columns
from app.services.tracing import flush as flush_traces


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        if "postgresql" in settings.database_url:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            try:
                await conn.execute(text("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'overdue'"))
            except Exception:
                pass
        await conn.run_sync(Base.metadata.create_all)
        if settings.database_url.startswith("sqlite"):
            await conn.run_sync(sync_missing_columns)
    yield
    flush_traces()
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(employees.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(logs.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
