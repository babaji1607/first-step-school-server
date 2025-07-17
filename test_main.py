import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["name"] == "Student Attendance API"

@pytest.mark.asyncio
async def test_api_info_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api-info")
        assert response.status_code == 200
        data = response.json()
        assert data["api"] == "Student Attendance API"
        assert "endpoints" in data
        assert any(e["path"] == "/" for e in data["endpoints"])

@pytest.mark.asyncio
async def test_health_patch_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch("/health")
        assert response.status_code == 200
        assert response.json() == {"message": "server is running"}
