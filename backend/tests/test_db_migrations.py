import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import Base
from app.db_migrations import sync_missing_columns
import app.models  # noqa: F401


@pytest.mark.asyncio
async def test_sync_missing_columns_adds_project_tech_stack():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "CREATE TABLE projects_legacy AS SELECT "
                "id, name, description, idea, business_objective, department_id, "
                "project_type, priority, expected_deadline, classification, "
                "known_technologies, business_constraints, technical_constraints, "
                "status, created_by_id, current_version, created_at, updated_at "
                "FROM projects"
            )
        )
        await conn.execute(text("DROP TABLE projects"))
        await conn.execute(text("ALTER TABLE projects_legacy RENAME TO projects"))

        def _column_names(connection):
            return {column["name"] for column in inspect(connection).get_columns("projects")}

        await conn.run_sync(sync_missing_columns)
        columns = await conn.run_sync(_column_names)

    assert "frontend_technology" in columns
    assert "backend_technology" in columns
    assert "database_technology" in columns

    await engine.dispose()
