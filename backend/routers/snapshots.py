"""
routers/snapshots.py

Endpoints for snapshots, SSE progress streaming, and graph data.

Endpoints
---------
POST   /api/v1/projects/{project_id}/snapshots    Trigger analysis (background task)
GET    /api/v1/projects/{project_id}/snapshots    List snapshots for a project
GET    /api/v1/snapshots/{snapshot_id}            Get snapshot detail + status
GET    /api/v1/snapshots/{snapshot_id}/progress   SSE progress stream
GET    /api/v1/snapshots/{snapshot_id}/graph      Full graph data (nodes + edges)
"""
import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Optional, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db, AsyncSessionLocal
from models import Project, Snapshot, FileNode, DependencyEdge, AISummary
from workers.progress_store import create_queue, get_queue
from workers.analysis_worker import run_analysis
from services.ai_service import generate_code_summary

router = APIRouter(tags=["snapshots"])

# ---------------------------------------------------------------------------
# Snapshot sub-resource under /api/v1/projects/{project_id}/snapshots
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/projects/{project_id}/snapshots",
    status_code=202,
    summary="Trigger analysis for a project",
)
async def create_snapshot(
    project_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """
    Creates a Snapshot row (status=pending), registers a progress queue,
    launches the analysis as a background task, and returns immediately
    with the snapshot_id.

    The client should then connect to GET /snapshots/{id}/progress to
    follow the SSE stream, or poll GET /snapshots/{id} for status.
    """
    # Verify project exists
    proj_result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = proj_result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    # Create the snapshot record
    snapshot = Snapshot(
        id=str(uuid.uuid4()),
        project_id=project_id,
        status="pending",
    )
    session.add(snapshot)
    await session.commit()

    # Register the SSE queue BEFORE launching the task so the client
    # can connect to /progress without a race condition
    queue = create_queue(snapshot.id)

    # Launch analysis in the background — returns 202 Accepted immediately
    background_tasks.add_task(
        run_analysis,
        snapshot_id=snapshot.id,
        project_path=project.path,
        queue=queue,
    )

    return {
        "snapshot_id": snapshot.id,
        "project_id": project_id,
        "status": "pending",
        "progress_url": f"/api/v1/snapshots/{snapshot.id}/progress",
        "graph_url": f"/api/v1/snapshots/{snapshot.id}/graph",
    }


@router.get(
    "/api/v1/projects/{project_id}/snapshots",
    summary="List all snapshots for a project",
)
async def list_snapshots(
    project_id: str,
    session: AsyncSession = Depends(get_db),
):
    # Verify project exists
    proj_result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    if proj_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    result = await session.execute(
        select(Snapshot)
        .where(Snapshot.project_id == project_id)
        .order_by(desc(Snapshot.created_at))
    )
    snapshots = result.scalars().all()

    return {
        "snapshots": [_snapshot_to_dict(s) for s in snapshots],
        "total": len(snapshots),
    }


# ---------------------------------------------------------------------------
# Snapshot resource at /api/v1/snapshots/{snapshot_id}
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/snapshots/{snapshot_id}",
    summary="Get snapshot detail and status",
)
async def get_snapshot(
    snapshot_id: str,
    session: AsyncSession = Depends(get_db),
):
    snapshot = await _get_snapshot_or_404(snapshot_id, session)

    # Count persisted nodes for progress context
    nodes_result = await session.execute(
        select(FileNode).where(FileNode.snapshot_id == snapshot_id)
    )
    node_count = len(nodes_result.scalars().all())

    return {**_snapshot_to_dict(snapshot), "file_count": node_count}


@router.get(
    "/api/v1/snapshots/{snapshot_id}/progress",
    summary="SSE stream — real-time analysis progress",
)
async def snapshot_progress(
    snapshot_id: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Server-Sent Events stream for analysis progress (AD-007).

    Event format:
        data: {"type": "progress", "stage": "...", "pct": 0-100, "message": "..."}
        data: {"type": "done", "snapshot_id": "..."}
        data: {"type": "error", "message": "..."}

    The stream closes automatically after a "done" or "error" event.
    A keep-alive comment (`: ping`) is sent every 15 s to prevent proxy timeouts.
    """
    snapshot = await _get_snapshot_or_404(snapshot_id, session)

    # If already finished, emit a single terminal event and close immediately
    if snapshot.status == "completed":
        async def _instant_done():
            yield _sse({"type": "done", "snapshot_id": snapshot_id})
        return StreamingResponse(
            _instant_done(),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )

    if snapshot.status == "failed":
        async def _instant_error():
            yield _sse({"type": "error", "message": snapshot.error_message or "Analysis failed"})
        return StreamingResponse(
            _instant_error(),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )

    # Still in-flight — stream from the queue
    queue = get_queue(snapshot_id)

    async def _stream():
        # If the queue doesn't exist yet (very tight race), poll DB briefly
        if queue is None:
            for _ in range(10):
                await asyncio.sleep(0.5)
                q = get_queue(snapshot_id)
                if q is not None:
                    break
            else:
                # Give up and ask the client to poll /snapshots/{id} instead
                yield _sse({"type": "error", "message": "Progress stream unavailable. Poll /snapshots/{id} for status."})
                return

        active_queue = get_queue(snapshot_id) or queue

        while True:
            try:
                # Wait up to 15 s; if nothing arrives send a keep-alive ping
                event = await asyncio.wait_for(active_queue.get(), timeout=15.0)
                yield _sse(event)
                if event.get("type") in ("done", "error"):
                    break
            except asyncio.TimeoutError:
                # SSE keep-alive comment — prevents proxies from closing the connection
                yield ": ping\n\n"

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


@router.get(
    "/api/v1/snapshots/{snapshot_id}/graph",
    summary="Get full graph data (nodes + edges) for a completed snapshot",
)
async def get_graph(
    snapshot_id: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Returns all FileNode and DependencyEdge records for a completed snapshot
    in a shape ready for React Flow (Phase 5).

    Nodes contain: id, file_path, node_type, language, metrics, imports, functions
    Edges contain: id, source (node_id), target (node_id), import_string, edge_type
    """
    snapshot = await _get_snapshot_or_404(snapshot_id, session)

    if snapshot.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Graph is not available yet — snapshot status is '{snapshot.status}'.",
        )

    # Load nodes
    nodes_result = await session.execute(
        select(FileNode)
        .where(FileNode.snapshot_id == snapshot_id)
        .order_by(FileNode.file_path)
    )
    file_nodes = nodes_result.scalars().all()

    # Load edges
    edges_result = await session.execute(
        select(DependencyEdge).where(DependencyEdge.snapshot_id == snapshot_id)
    )
    edges = edges_result.scalars().all()

    return {
        "snapshot_id": snapshot_id,
        "node_count": len(file_nodes),
        "edge_count": len(edges),
        "nodes": [
            {
                "id": n.id,
                "file_path": n.file_path,
                "node_type": n.node_type,
                "language": n.language,
                "metrics": n.metrics or {},
                "imports": n.imports or [],
                "functions": n.functions or [],
                "pos_x": n.pos_x,
                "pos_y": n.pos_y,
            }
            for n in file_nodes
        ],
        "edges": [
            {
                "id": e.id,
                "source": e.source_node_id,
                "target": e.target_node_id,
                "import_string": e.import_string,
                "edge_type": e.edge_type,
            }
            for e in edges
        ],
    }


@router.get(
    "/api/v1/snapshots/{snapshot_id}/nodes/{node_id}/summary",
    summary="Generate or retrieve an AI summary for a specific file node",
)
async def get_node_summary(
    snapshot_id: str,
    node_id: str,
    session: AsyncSession = Depends(get_db),
):
    snapshot = await _get_snapshot_or_404(snapshot_id, session)

    # 1. Fetch FileNode
    node_result = await session.execute(
        select(FileNode).where(FileNode.id == node_id, FileNode.snapshot_id == snapshot_id)
    )
    file_node = node_result.scalar_one_or_none()
    if not file_node:
        raise HTTPException(status_code=404, detail="File node not found")
        
    if file_node.node_type == "dir":
        raise HTTPException(status_code=400, detail="Cannot summarize directories")

    project_id = snapshot.project_id
    
    # 2. Check if summary exists in DB (Cache hit)
    summary_result = await session.execute(
        select(AISummary).where(
            AISummary.project_id == project_id,
            AISummary.content_hash == file_node.content_hash,
            AISummary.file_path == file_node.file_path
        )
    )
    cached_summary = summary_result.scalar_one_or_none()
    
    if cached_summary:
        return {"summary": cached_summary.summary_text, "cached": True}
        
    # 3. Read file content
    proj_result = await session.execute(select(Project).where(Project.id == project_id))
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    abs_path = os.path.join(project.path, file_node.file_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File does not exist on disk")
        
    try:
        # Limit to 50KB to avoid massive prompt sizes
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read(50000)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")
        
    # 4. Call AI Service
    summary_text = await generate_code_summary(content)
    
    # 5. Save to cache
    new_summary = AISummary(
        project_id=project_id,
        file_path=file_node.file_path,
        content_hash=file_node.content_hash,
        summary_text=summary_text
    )
    session.add(new_summary)
    await session.commit()
    
    return {"summary": summary_text, "cached": False}


# ---------------------------------------------------------------------------
# Node position persistence (PATCH)
# ---------------------------------------------------------------------------

class NodePosition(BaseModel):
    x: float
    y: float


@router.patch(
    "/api/v1/snapshots/{snapshot_id}/graph/positions",
    summary="Persist manually-positioned node coordinates",
)
async def save_graph_positions(
    snapshot_id: str,
    positions: Dict[str, NodePosition] = Body(..., description="{node_id: {x, y}}"),
    session: AsyncSession = Depends(get_db),
):
    """
    Saves canvas positions for one or more nodes so the layout is preserved
    between sessions. Only nodes present in `positions` are updated (partial update).
    """
    snapshot = await _get_snapshot_or_404(snapshot_id, session)

    if snapshot.status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Cannot save positions for a snapshot that is not completed.",
        )

    updated = 0
    for node_id, pos in positions.items():
        result = await session.execute(
            select(FileNode).where(
                FileNode.id == node_id,
                FileNode.snapshot_id == snapshot_id,
            )
        )
        node = result.scalar_one_or_none()
        if node:
            node.pos_x = pos.x
            node.pos_y = pos.y
            updated += 1

    await session.commit()
    return {"updated": updated}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _snapshot_to_dict(s: Snapshot) -> dict:
    return {
        "id": s.id,
        "project_id": s.project_id,
        "status": s.status,
        "error_message": s.error_message,
        "created_at": s.created_at,
        "completed_at": s.completed_at,
    }


async def _get_snapshot_or_404(snapshot_id: str, session: AsyncSession) -> Snapshot:
    result = await session.execute(
        select(Snapshot).where(Snapshot.id == snapshot_id)
    )
    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"Snapshot '{snapshot_id}' not found.")
    return snapshot


def _sse(event: dict) -> str:
    """Format a dict as a well-formed SSE data frame."""
    return f"data: {json.dumps(event)}\n\n"


def _sse_headers() -> dict:
    return {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",          # Disable nginx buffering
        "Connection": "keep-alive",
    }
