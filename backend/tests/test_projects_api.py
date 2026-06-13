"""
tests/test_projects_api.py

Integration tests for Phase 3 endpoints:
  - Project CRUD (/api/v1/projects)
  - Snapshot creation (/api/v1/projects/{id}/snapshots)
  - Snapshot status (/api/v1/snapshots/{id})

Tests use an in-memory async test client via httpx + ASGITransport.
The DB is the same SQLite file as the app; we clean up created records
using the DELETE endpoint so tests are self-contained.
"""
import pytest
import os
from httpx import AsyncClient, ASGITransport
from main import app

BASE = "http://test"


@pytest.mark.anyio
async def test_list_projects_empty():
    """GET /api/v1/projects returns a valid (possibly empty) list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        r = await c.get("/api/v1/projects")
    assert r.status_code == 200
    body = r.json()
    assert "projects" in body
    assert "total" in body


@pytest.mark.anyio
async def test_create_project_invalid_path():
    """Registering a project with a non-existent path returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        r = await c.post("/api/v1/projects", json={
            "name": "Ghost",
            "path": "/this/path/definitely/does/not/exist/12345",
        })
    assert r.status_code == 422  # Pydantic validator rejects it


@pytest.mark.anyio
async def test_create_and_delete_project(tmp_path):
    """Full lifecycle: create a project, verify it appears, then delete it."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        # Create
        r = await c.post("/api/v1/projects", json={
            "name": "Test Project",
            "path": str(tmp_path),
        })
        assert r.status_code == 201, r.text
        project = r.json()
        project_id = project["id"]
        assert project["name"] == "Test Project"
        assert project["path"] == str(tmp_path)

        # It shows up in the list
        r2 = await c.get("/api/v1/projects")
        ids = [p["id"] for p in r2.json()["projects"]]
        assert project_id in ids

        # Get detail
        r3 = await c.get(f"/api/v1/projects/{project_id}")
        assert r3.status_code == 200
        assert r3.json()["id"] == project_id

        # Delete
        r4 = await c.delete(f"/api/v1/projects/{project_id}")
        assert r4.status_code == 204

        # Confirm gone
        r5 = await c.get(f"/api/v1/projects/{project_id}")
        assert r5.status_code == 404


@pytest.mark.anyio
async def test_duplicate_project_path(tmp_path):
    """Registering the same path twice returns 409 Conflict."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        r1 = await c.post("/api/v1/projects", json={"name": "A", "path": str(tmp_path)})
        assert r1.status_code == 201
        project_id = r1.json()["id"]

        r2 = await c.post("/api/v1/projects", json={"name": "B", "path": str(tmp_path)})
        assert r2.status_code == 409

        # Cleanup
        await c.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.anyio
async def test_get_nonexistent_project():
    """GET on a random UUID returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        r = await c.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_update_project_config(tmp_path):
    """PATCH /config updates the analysis config fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        r = await c.post("/api/v1/projects", json={"name": "Cfg Test", "path": str(tmp_path)})
        project_id = r.json()["id"]

        r2 = await c.patch(f"/api/v1/projects/{project_id}/config", json={
            "excluded_dirs": ["tests", "docs"],
            "max_file_size_kb": 200,
        })
        assert r2.status_code == 200
        cfg = r2.json()
        assert "tests" in cfg["excluded_dirs"]
        assert cfg["max_file_size_kb"] == 200

        # Cleanup
        await c.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.anyio
async def test_create_snapshot_returns_immediately(tmp_path):
    """
    POST /projects/{id}/snapshots must return 202 immediately with a snapshot_id.
    The actual analysis runs in the background — we don't wait for it here.
    """
    # Write a tiny Python file so the orchestrator has something to parse
    (tmp_path / "hello.py").write_text("import os\ndef hi(): pass\n")

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        # Register project
        r = await c.post("/api/v1/projects", json={"name": "Snap Test", "path": str(tmp_path)})
        project_id = r.json()["id"]

        # Trigger analysis
        r2 = await c.post(f"/api/v1/projects/{project_id}/snapshots")
        assert r2.status_code == 202, r2.text
        body = r2.json()
        assert "snapshot_id" in body
        assert body["status"] == "pending"
        assert "/progress" in body["progress_url"]
        assert "/graph" in body["graph_url"]

        snapshot_id = body["snapshot_id"]

        # Snapshot detail is retrievable
        r3 = await c.get(f"/api/v1/snapshots/{snapshot_id}")
        assert r3.status_code == 200
        assert r3.json()["id"] == snapshot_id

        # Cleanup (cascade deletes snapshots + nodes)
        await c.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.anyio
async def test_snapshot_for_nonexistent_project():
    """POST /projects/{fake_id}/snapshots returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        r = await c.post("/api/v1/projects/00000000-0000-0000-0000-000000000000/snapshots")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_graph_on_pending_snapshot(tmp_path):
    """GET /snapshots/{id}/graph returns 409 when snapshot is not completed yet."""
    import uuid
    from database import AsyncSessionLocal
    from models import Project, Snapshot

    async with AsyncSessionLocal() as db:
        project_id = str(uuid.uuid4())
        snapshot_id = str(uuid.uuid4())
        db.add(Project(id=project_id, name="Race Test", path=str(tmp_path)))
        db.add(Snapshot(id=snapshot_id, project_id=project_id, status="pending"))
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        # Graph not available while still pending/processing
        r3 = await c.get(f"/api/v1/snapshots/{snapshot_id}/graph")
        assert r3.status_code == 409

        # Cleanup
        await c.delete(f"/api/v1/projects/{project_id}")
