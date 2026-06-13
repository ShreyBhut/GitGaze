"""
main.py — GitGaze FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers.analysis import router as analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup: create all SQLAlchemy tables if they don't exist.
    This is idempotent — safe to call every time the server starts.
    """
    async with engine.begin() as conn:
        # Import models so SQLAlchemy is aware of them before create_all
        import models  # noqa: F401, PLC0415
        await conn.run_sync(Base.metadata.create_all)

    yield
    # (teardown code here if needed in the future)


def create_app() -> FastAPI:
    app = FastAPI(
        title="GitGaze API",
        description="Repository Analysis & Visualization System",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Health check (no router needed, lives here) ---
    @app.get("/health", tags=["meta"])
    async def health_check():
        return {"status": "ok", "service": "GitGaze Backend"}

    # --- Feature routers ---
    app.include_router(analysis_router)

    return app


app = create_app()