"""
routers/projects.py

CRUD endpoints for the /api/v1/projects resource.

Endpoints
---------
GET    /api/v1/projects                  List all registered projects
POST   /api/v1/projects                  Register a new project
GET    /api/v1/projects/{id}             Get project detail + latest snapshot status
DELETE /api/v1/projects/{id}             Remove project (cascades to all its data)
PATCH  /api/v1/projects/{id}/config      Update per-project analysis configuration
"""
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models import Project, Snapshot, AnalysisConfig

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str
    path: str

    @field_validator("path")
    @classmethod
    def path_must_exist(cls, v: str) -> str:
        v = v.strip()
        if not os.path.exists(v):
            raise ValueError(f"Path does not exist on the server: {v}")
        if not os.path.isdir(v):
            raise ValueError("Path must be a directory, not a file.")
        return v

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name must not be empty.")
        return v


class AnalysisConfigUpdate(BaseModel):
    excluded_dirs: Optional[List[str]] = None
    enabled_languages: Optional[List[str]] = None
    max_file_size_kb: Optional[int] = None


class SnapshotStatusSummary(BaseModel):
    id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    path: str
    created_at: datetime
    latest_snapshot: Optional[SnapshotStatusSummary] = None


class AnalysisConfigResponse(BaseModel):
    excluded_dirs: List[str]
    enabled_languages: List[str]
    max_file_size_kb: int


class ProjectDetailResponse(ProjectResponse):
    config: Optional[AnalysisConfigResponse] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_project_or_404(project_id: str, session: AsyncSession) -> Project:
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return project


async def _latest_snapshot(project_id: str, session: AsyncSession) -> Optional[Snapshot]:
    result = await session.execute(
        select(Snapshot)
        .where(Snapshot.project_id == project_id)
        .order_by(desc(Snapshot.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


def _project_to_response(
    project: Project,
    latest: Optional[Snapshot] = None,
    config: Optional[AnalysisConfig] = None,
) -> dict:
    data: dict = {
        "id": project.id,
        "name": project.name,
        "path": project.path,
        "created_at": project.created_at,
        "latest_snapshot": {
            "id": latest.id,
            "status": latest.status,
            "created_at": latest.created_at,
            "completed_at": latest.completed_at,
        } if latest else None,
    }
    if config is not None:
        data["config"] = {
            "excluded_dirs": config.excluded_dirs or [],
            "enabled_languages": config.enabled_languages or [],
            "max_file_size_kb": config.max_file_size_kb,
        }
    return data


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", summary="List all projects")
async def list_projects(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Project).order_by(desc(Project.created_at)))
    projects = result.scalars().all()

    items = []
    for p in projects:
        latest = await _latest_snapshot(p.id, session)
        items.append(_project_to_response(p, latest))
    return {"projects": items, "total": len(items)}


@router.post("", status_code=201, summary="Register a new project")
async def create_project(
    body: ProjectCreate,
    session: AsyncSession = Depends(get_db),
):
    # Check for existing project at the same path
    existing = await session.execute(
        select(Project).where(Project.path == body.path)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A project already exists for path: {body.path}",
        )

    project = Project(
        id=str(uuid.uuid4()),
        name=body.name,
        path=body.path,
    )
    session.add(project)

    # Create a default AnalysisConfig for the project
    config = AnalysisConfig(
        id=str(uuid.uuid4()),
        project_id=project.id,
        excluded_dirs=[],
        enabled_languages=[],
        max_file_size_kb=500,
    )
    session.add(config)
    await session.commit()

    return _project_to_response(project, config=config)


@router.get("/{project_id}", summary="Get project detail")
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(project_id, session)
    latest = await _latest_snapshot(project_id, session)

    config_result = await session.execute(
        select(AnalysisConfig).where(AnalysisConfig.project_id == project_id)
    )
    config = config_result.scalar_one_or_none()

    return _project_to_response(project, latest, config)


@router.delete("/{project_id}", status_code=204, summary="Delete a project")
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(project_id, session)
    await session.delete(project)
    await session.commit()
    # 204 No Content — return nothing


@router.patch("/{project_id}/config", summary="Update analysis configuration")
async def update_config(
    project_id: str,
    body: AnalysisConfigUpdate,
    session: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, session)

    config_result = await session.execute(
        select(AnalysisConfig).where(AnalysisConfig.project_id == project_id)
    )
    config = config_result.scalar_one_or_none()

    if config is None:
        # Lazily create config if it wasn't created with the project
        config = AnalysisConfig(
            id=str(uuid.uuid4()),
            project_id=project_id,
            excluded_dirs=[],
            enabled_languages=[],
            max_file_size_kb=500,
        )
        session.add(config)

    if body.excluded_dirs is not None:
        config.excluded_dirs = body.excluded_dirs
    if body.enabled_languages is not None:
        config.enabled_languages = body.enabled_languages
    if body.max_file_size_kb is not None:
        config.max_file_size_kb = body.max_file_size_kb

    await session.commit()

    return {
        "excluded_dirs": config.excluded_dirs,
        "enabled_languages": config.enabled_languages,
        "max_file_size_kb": config.max_file_size_kb,
    }
