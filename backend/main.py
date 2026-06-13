"""
main.py — GitGaze FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers.analysis import router as legacy_analysis_router
from routers.projects import router as projects_router
from routers.snapshots import router as snapshots_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: create all SQLAlchemy tables if they don't exist (idempotent).
    """
    async with engine.begin() as conn:
        import models  # noqa: F401, PLC0415 — registers all ORM classes with Base
        await conn.run_sync(Base.metadata.create_all)

    yield
    # Teardown hooks go here when needed (e.g., flush queues, close connections)


def create_app() -> FastAPI:
    app = FastAPI(
        title="GitGaze API",
        description="Repository Analysis & Visualization System",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Health check ---
    @app.get("/health", tags=["meta"])
    async def health_check():
        return {"status": "ok", "service": "GitGaze Backend", "version": "0.2.0"}

    # --- v1 API routers ---
    app.include_router(projects_router)   # /api/v1/projects
    app.include_router(snapshots_router)  # /api/v1/snapshots + /api/v1/projects/{id}/snapshots

    # --- Legacy Phase 2 endpoint (kept for backward compat, will be removed in Phase 7) ---
    app.include_router(legacy_analysis_router)  # /api/analyze

    return app


app = create_app()