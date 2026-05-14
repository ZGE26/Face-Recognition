import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.database import Base, engine

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Face Recognition API",
    version="1.0.0",
    description="Realtime face recognition — register users and scan faces against the database.",
    lifespan=lifespan,
)

app.include_router(v1_router, prefix="/api/v1")
