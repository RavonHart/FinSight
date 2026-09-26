import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data


@pytest.mark.asyncio
async def test_liveness_endpoint(client: AsyncClient):
    response = await client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "live"}


@pytest.mark.asyncio
async def test_api_status_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "FinSight API"
    assert data["version"] == "0.1.0"
