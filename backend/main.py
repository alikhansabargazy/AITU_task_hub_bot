from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.tasks import router as tasks_router
from backend.api.auth import router as auth_router
from backend.api.profile import router as profile_router
from backend.api.schedule import router as schedule_router
from backend.api.dashboard import router as dashboard_router
from database import models


@asynccontextmanager
async def lifespan(_: FastAPI):
    await models.async_main()
    yield
    await models.engine.dispose()


app = FastAPI(
    title="AITU TaskHub API",
    version="0.2.0",
    description="Standalone TaskHub accounts, tasks, schedule, dashboard and settings. No bot required.",
    lifespan=lifespan,
)
for router in (auth_router, profile_router, tasks_router, schedule_router, dashboard_router):
    app.include_router(router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_error(_, error: RequestValidationError):
    # Never reflect submitted passwords/tokens in validation error bodies.
    details = [{key: item[key] for key in ("loc", "msg", "type")} for item in error.errors()]
    return JSONResponse(status_code=422, content={"detail": details})


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "taskhub-api"}
