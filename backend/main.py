from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.tasks import router as tasks_router
from database import models


@asynccontextmanager
async def lifespan(_: FastAPI):
    await models.async_main()
    yield
    await models.engine.dispose()


app = FastAPI(
    title="AITU TaskHub API",
    version="0.1.0",
    description="Backend shared by the Android application and Telegram bot.",
    lifespan=lifespan,
)
app.include_router(tasks_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "taskhub-api"}
