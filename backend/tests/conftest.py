import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.security import hash_password
from app.config import settings
from app.models import Base, User, UserRole


@pytest.fixture(autouse=True)
def disable_external_project_memory(monkeypatch):
    """Keep tests deterministic; Chroma integration is covered with a fake collection."""
    monkeypatch.setattr(settings, "project_memory_enabled", False)


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def manager_user(db_session: AsyncSession):
    user = User(
        email="manager@test.com",
        hashed_password=hash_password("secret"),
        full_name="Test Manager",
        role=UserRole.MANAGER,
    )
    db_session.add(user)
    await db_session.flush()
    return user
