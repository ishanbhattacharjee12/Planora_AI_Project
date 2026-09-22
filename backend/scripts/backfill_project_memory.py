"""Create or refresh semantic memory records for projects that already exist."""

import asyncio

from sqlalchemy import select

from app.database import Base, async_session, engine
from app.db_migrations import sync_missing_columns
from app.models import Project
from app.services.project_memory import upsert_project_memory


async def main() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        if engine.url.drivername.startswith("sqlite"):
            await connection.run_sync(sync_missing_columns)

    async with async_session() as db:
        projects = list((await db.execute(select(Project))).scalars().all())
        for project in projects:
            memory = await upsert_project_memory(db, project)
            print(f"{project.id}: {project.name} [{memory.index_status}]")
        await db.commit()
        print(f"Backfilled {len(projects)} project memories.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
