"""Student endpoint tests."""

import pytest
from httpx import AsyncClient


class TestStudentList:
    """Tests for listing students."""

    @pytest.mark.asyncio
    async def test_list_students_empty(self, client: AsyncClient, auth_headers):
        """Test listing students when none exist."""
        response = await client.get("/v1/students", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_students_with_data(
        self, client: AsyncClient, auth_headers, test_student
    ):
        """Test listing students with existing data."""
        response = await client.get("/v1/students", headers=auth_headers)
        assert response.status_code == 200
        students = response.json()
        assert len(students) == 1
        assert students[0]["full_name"] == "Test Student"
        assert students[0]["instrument"] == "Piano"

    @pytest.mark.asyncio
    async def test_list_students_unauthenticated(self, client: AsyncClient, db_session):
        """Test listing students without auth fails."""
        response = await client.get("/v1/students")
        # FastAPI HTTPBearer returns 401 for missing credentials
        assert response.status_code == 401


class TestStudentCreate:
    """Tests for creating students."""

    @pytest.mark.asyncio
    async def test_create_student_success(self, client: AsyncClient, auth_headers):
        """Test successful student creation."""
        response = await client.post(
            "/v1/students",
            headers=auth_headers,
            json={
                "full_name": "New Student",
                "instrument": "Violin",
                "level": "BEGINNER",
                "parent_email": "newparent@example.com",
                "notes": "New student notes",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "New Student"
        assert data["instrument"] == "Violin"
        assert data["level"] == "BEGINNER"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_student_minimal(self, client: AsyncClient, auth_headers):
        """Test creating student with minimal fields."""
        response = await client.post(
            "/v1/students",
            headers=auth_headers,
            json={
                "full_name": "Minimal Student",
                "instrument": "Guitar",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "Minimal Student"
        assert data["parent_email"] is None

    @pytest.mark.asyncio
    async def test_create_student_missing_name(self, client: AsyncClient, auth_headers):
        """Test creating student without name fails."""
        response = await client.post(
            "/v1/students",
            headers=auth_headers,
            json={"instrument": "Piano"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_student_unauthenticated(
        self, client: AsyncClient, db_session
    ):
        """Test creating student without auth fails."""
        response = await client.post(
            "/v1/students",
            json={
                "full_name": "Unauth Student",
                "instrument": "Drums",
            },
        )
        assert response.status_code == 401


class TestStudentDetail:
    """Tests for getting student details."""

    @pytest.mark.asyncio
    async def test_get_student_success(
        self, client: AsyncClient, auth_headers, test_student
    ):
        """Test getting student details."""
        response = await client.get(
            f"/v1/students/{test_student.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Test Student"
        assert data["instrument"] == "Piano"

    @pytest.mark.asyncio
    async def test_get_student_not_found(self, client: AsyncClient, auth_headers):
        """Test getting nonexistent student fails."""
        response = await client.get(
            "/v1/students/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_student_unauthenticated(
        self, client: AsyncClient, test_student
    ):
        """Test getting student without auth fails."""
        response = await client.get(f"/v1/students/{test_student.id}")
        assert response.status_code == 401


class TestStudentUpdate:
    """Tests for updating students."""

    @pytest.mark.asyncio
    async def test_update_student_success(
        self, client: AsyncClient, auth_headers, test_student
    ):
        """Test successful student update."""
        response = await client.patch(
            f"/v1/students/{test_student.id}",
            headers=auth_headers,
            json={
                "full_name": "Updated Student",
                "instrument": "Cello",
                "level": "ADVANCED",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Student"
        assert data["instrument"] == "Cello"

    @pytest.mark.asyncio
    async def test_update_student_partial(
        self, client: AsyncClient, auth_headers, test_student
    ):
        """Test partial student update."""
        response = await client.patch(
            f"/v1/students/{test_student.id}",
            headers=auth_headers,
            json={"notes": "Updated notes only"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes only"
        assert data["full_name"] == "Test Student"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_student_not_found(self, client: AsyncClient, auth_headers):
        """Test updating nonexistent student fails."""
        response = await client.patch(
            "/v1/students/nonexistent-id",
            headers=auth_headers,
            json={"full_name": "Ghost"},
        )
        assert response.status_code == 404


class TestStudentArchive:
    """Tests for archiving students."""

    @pytest.mark.asyncio
    async def test_archive_student_success(
        self, client: AsyncClient, auth_headers, test_student
    ):
        """Test successful student archiving."""
        response = await client.post(
            f"/v1/students/{test_student.id}/archive",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] == True

    @pytest.mark.asyncio
    async def test_archive_student_not_found(self, client: AsyncClient, auth_headers):
        """Test archiving nonexistent student fails."""
        response = await client.post(
            "/v1/students/nonexistent-id/archive",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestStudentInstruments:
    """Tests for instruments endpoint."""

    @pytest.mark.asyncio
    async def test_get_instruments(self, client: AsyncClient, db_session):
        """Test getting list of instruments."""
        response = await client.get("/v1/students/instruments")
        assert response.status_code == 200
        data = response.json()
        assert "instruments" in data
        assert "Piano" in data["instruments"]
        assert "Violin" in data["instruments"]
