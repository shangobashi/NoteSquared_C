"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


class TestHealth:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient, db_session):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient, db_session):
        """Test root endpoint returns app info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Note²" in data["name"]
        assert data["version"] == "1.0.0"
        assert "docs" in data
