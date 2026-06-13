"""
routers/analysis.py

Houses the /api/analyze endpoint.
Currently supports the Phase 2 direct analysis path:
  POST /api/analyze  →  runs analysis synchronously, persists to DB, returns structured data.

Future phases will replace this with:
  POST /projects/{id}/snapshots  (triggers background task, returns job_id immediately)
"""
import os
import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Project, Snapshot
from analysis.orchestrator import AnalyzerOrchestrator

router = APIRouter(prefix="/api", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    path: str
    project_name: str = ""   # optional friendly name; defaults to the directory name


@router.post("/analyze")
async def analyze_repository(
    request: AnalyzeRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Takes a local repository path, runs the core analysis engine,
    persists an immutable Snapshot + FileNode records to SQLite,
    and returns structured repository data.
    """
    repo_path = request.path.strip()

    if not os.path.exists(repo_path):
        raise HTTPException(
            status_code=400,
            detail=f"Repository path does not exist on the server: {repo_path}",
        )

    if not os.path.isdir(repo_path):
        raise HTTPException(
            status_code=400,
            detail="Path must point to a directory, not a file.",
        )

    # --- Upsert Project ---
    result = await session.execute(
        select(Project).where(Project.path == repo_path)
    )
    project = result.scalar_one_or_none()

    if project is None:
        name = request.project_name or os.path.basename(repo_path.rstrip("/\\"))
        project = Project(id=str(uuid.uuid4()), name=name, path=repo_path)
        session.add(project)
        await session.flush()

    # --- Create Snapshot (pending) ---
    snapshot = Snapshot(
        id=str(uuid.uuid4()),
        project_id=project.id,
        status="pending",
    )
    session.add(snapshot)
    await session.commit()

    # --- Run Analysis (synchronous for now; Phase 3 will move to background task) ---
    try:
        orchestrator = AnalyzerOrchestrator(repo_path)
        await orchestrator.analyze_and_persist(session, snapshot.id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    # --- Return the raw result dict for Phase 2 ---
    # Phase 5 (graph endpoint) will return the structured graph format instead
    orchestrator_sync = AnalyzerOrchestrator(repo_path)
    raw_data = orchestrator_sync.analyze_repo()

    return {
        "status": "success",
        "snapshot_id": snapshot.id,
        "project_id": project.id,
        "data": raw_data,
    }
