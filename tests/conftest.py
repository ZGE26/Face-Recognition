import os

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base
from app.models import user  # ensure ORM models are registered  # noqa: F401

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
FACE1_PATH = os.path.join(ASSETS_DIR, "face1.jpg")
FACE2_PATH = os.path.join(ASSETS_DIR, "face2.jpg")

_TEST_DB_URL = (
    f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)


@pytest_asyncio.fixture
async def db():
    """Async DB session — creates tables before each test and truncates them after."""
    engine = create_async_engine(_TEST_DB_URL, connect_args={"ssl": False})

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())
        await engine.dispose()
