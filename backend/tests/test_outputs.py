"""Output endpoint tests."""

import pytest
from httpx import AsyncClient


class TestOutputGet:
    """Tests for getting outputs."""

    @pytest.mark.asyncio
    async def test_get_output_success(
        self, client: AsyncClient, auth_headers, test_output
    ):
        """Test getting an output."""
        response = await client.get(
            f"/v1/outputs/{test_output.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["output_type"] == "STUDENT_RECAP"
        assert data["content"] is not None

    @pytest.mark.asyncio
    async def test_get_output_not_found(self, client: AsyncClient, auth_headers):
        """Test getting nonexistent output fails."""
        response = await client.get(
            "/v1/outputs/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestOutputUpdate:
    """Tests for updating outputs."""

    @pytest.mark.asyncio
    async def test_update_output_success(
        self, client: AsyncClient, auth_headers, test_output
    ):
        """Test successful output update."""
        response = await client.patch(
            f"/v1/outputs/{test_output.id}",
            headers=auth_headers,
            json={"content": "Updated content for the output"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content for the output"
        assert data["is_edited"] == True

    @pytest.mark.asyncio
    async def test_update_output_not_found(self, client: AsyncClient, auth_headers):
        """Test updating nonexistent output fails."""
        response = await client.patch(
            "/v1/outputs/nonexistent-id",
            headers=auth_headers,
            json={"content": "Some content"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_output_unauthenticated(
        self, client: AsyncClient, test_output
    ):
        """Test updating output without auth fails."""
        response = await client.patch(
            f"/v1/outputs/{test_output.id}",
            json={"content": "Unauthorized update"},
        )
        assert response.status_code == 401


class TestOutputShare:
    """Tests for marking outputs as shared."""

    @pytest.mark.asyncio
    async def test_share_output_success(
        self, client: AsyncClient, auth_headers, test_output
    ):
        """Test marking output as shared."""
        response = await client.post(
            f"/v1/outputs/{test_output.id}/share",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_shared"] == True

    @pytest.mark.asyncio
    async def test_share_output_not_found(self, client: AsyncClient, auth_headers):
        """Test sharing nonexistent output fails."""
        response = await client.post(
            "/v1/outputs/nonexistent-id/share",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestOutputRevert:
    """Tests for reverting outputs."""

    @pytest.mark.asyncio
    async def test_revert_output_success(
        self, client: AsyncClient, auth_headers, edited_output
    ):
        """Test successfully reverting an edited output."""
        response = await client.post(
            f"/v1/outputs/{edited_output.id}/revert",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Original practice plan content."
        assert data["is_edited"] == False

    @pytest.mark.asyncio
    async def test_revert_output_no_original(
        self, client: AsyncClient, auth_headers, test_output
    ):
        """Test reverting output without original content fails."""
        response = await client.post(
            f"/v1/outputs/{test_output.id}/revert",
            headers=auth_headers,
        )
        # Should fail since there's no original content
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_revert_output_not_found(self, client: AsyncClient, auth_headers):
        """Test reverting nonexistent output fails."""
        response = await client.post(
            "/v1/outputs/nonexistent-id/revert",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestOutputUnauthenticated:
    """Tests for output endpoints without authentication."""

    @pytest.mark.asyncio
    async def test_get_output_unauthenticated(self, client: AsyncClient, test_output):
        """Test getting output without auth fails."""
        response = await client.get(f"/v1/outputs/{test_output.id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_share_output_unauthenticated(self, client: AsyncClient, test_output):
        """Test sharing output without auth fails."""
        response = await client.post(f"/v1/outputs/{test_output.id}/share")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revert_output_unauthenticated(self, client: AsyncClient, test_output):
        """Test reverting output without auth fails."""
        response = await client.post(f"/v1/outputs/{test_output.id}/revert")
        assert response.status_code == 401
