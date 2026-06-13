import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.anyio
async def test_health_check():
    """Health endpoint must return 200 and status == 'ok'."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_analyze_invalid_path():
    """API must reject a non-existent repo path with HTTP 400."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Use "path" (not "repo_path") to match the API contract
        response = await client.post(
            "/api/analyze",
            json={"path": "/fake/nonexistent/repo/path"},
        )

    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]