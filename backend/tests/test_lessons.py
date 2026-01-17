"""Lesson endpoint tests."""

import pytest
from httpx import AsyncClient
from io import BytesIO
from unittest.mock import patch, AsyncMock


class TestLessonList:
    """Tests for listing lessons."""

    @pytest.mark.asyncio
    async def test_list_lessons_empty(
        self, client: AsyncClient, auth_headers, test_student
    ):
        """Test listing lessons when none exist."""
        response = await client.get(
            f"/v1/lessons?student_id={test_student.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_lessons_with_data(
        self, client: AsyncClient, auth_headers, test_lesson, test_student
    ):
        """Test listing lessons with existing data."""
        response = await client.get(
            f"/v1/lessons?student_id={test_student.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        lessons = response.json()
        assert len(lessons) == 1
        assert lessons[0]["status"] == "UPLOADED"

    @pytest.mark.asyncio
    async def test_list_all_lessons(
        self, client: AsyncClient, auth_headers, test_lesson
    ):
        """Test listing all lessons without student filter."""
        response = await client.get(
            "/v1/lessons",
            headers=auth_headers,
        )
        assert response.status_code == 200
        lessons = response.json()
        assert len(lessons) >= 1


class TestLessonCreate:
    """Tests for creating lessons."""

    @pytest.mark.asyncio
    async def test_create_lesson_success(
        self, client: AsyncClient, auth_headers, test_student
    ):
        """Test successful lesson creation."""
        response = await client.post(
            "/v1/lessons",
            headers=auth_headers,
            json={
                "student_id": test_student.id,
                "lesson_date": "2024-01-15",
            },
        )
        assert response.status_code == 201
        lesson = response.json()
        assert lesson["student_id"] == test_student.id
        assert lesson["status"] == "CREATED"
        assert "id" in lesson

    @pytest.mark.asyncio
    async def test_create_lesson_student_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test creating lesson for nonexistent student fails."""
        response = await client.post(
            "/v1/lessons",
            headers=auth_headers,
            json={
                "student_id": "nonexistent-id",
                "lesson_date": "2024-01-15",
            },
        )
        assert response.status_code == 404


class TestLessonUpload:
    """Tests for uploading audio to lessons."""

    @pytest.mark.asyncio
    @patch("app.routes.lessons.process_lesson_pipeline", new_callable=AsyncMock)
    async def test_upload_lesson_success(
        self, mock_pipeline, client: AsyncClient, auth_headers, test_student
    ):
        """Test successful lesson upload."""
        # First create a lesson
        create_response = await client.post(
            "/v1/lessons",
            headers=auth_headers,
            json={
                "student_id": test_student.id,
                "lesson_date": "2024-01-15",
            },
        )
        assert create_response.status_code == 201
        lesson_id = create_response.json()["id"]

        # Then upload audio
        audio_content = b"fake audio data for testing"
        files = {"audio": ("test_audio.m4a", BytesIO(audio_content), "audio/mp4")}

        response = await client.post(
            f"/v1/lessons/{lesson_id}/upload",
            headers=auth_headers,
            files=files,
        )
        assert response.status_code == 200
        lesson = response.json()
        assert lesson["status"] == "UPLOADED"
        assert lesson["id"] == lesson_id

    @pytest.mark.asyncio
    async def test_upload_lesson_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test uploading to nonexistent lesson fails."""
        audio_content = b"fake audio data"
        files = {"audio": ("test.m4a", BytesIO(audio_content), "audio/mp4")}

        response = await client.post(
            "/v1/lessons/nonexistent-id/upload",
            headers=auth_headers,
            files=files,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_invalid_audio_format(
        self, client: AsyncClient, auth_headers, test_student
    ):
        """Test uploading invalid audio format fails."""
        # First create a lesson
        create_response = await client.post(
            "/v1/lessons",
            headers=auth_headers,
            json={
                "student_id": test_student.id,
                "lesson_date": "2024-01-15",
            },
        )
        lesson_id = create_response.json()["id"]

        # Try to upload invalid format
        files = {"audio": ("test.txt", BytesIO(b"not audio"), "text/plain")}

        response = await client.post(
            f"/v1/lessons/{lesson_id}/upload",
            headers=auth_headers,
            files=files,
        )
        assert response.status_code == 400


class TestLessonDetail:
    """Tests for getting lesson details."""

    @pytest.mark.asyncio
    async def test_get_lesson_success(
        self, client: AsyncClient, auth_headers, test_lesson
    ):
        """Test getting lesson details."""
        response = await client.get(
            f"/v1/lessons/{test_lesson.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UPLOADED"
        assert "outputs" in data

    @pytest.mark.asyncio
    async def test_get_lesson_not_found(self, client: AsyncClient, auth_headers):
        """Test getting nonexistent lesson fails."""
        response = await client.get(
            "/v1/lessons/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_completed_lesson(
        self, client: AsyncClient, auth_headers, completed_lesson
    ):
        """Test getting completed lesson with transcript."""
        response = await client.get(
            f"/v1/lessons/{completed_lesson.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["transcript"] is not None


class TestLessonStatus:
    """Tests for lesson status endpoint."""

    @pytest.mark.asyncio
    async def test_get_lesson_status(
        self, client: AsyncClient, auth_headers, test_lesson
    ):
        """Test getting lesson status."""
        response = await client.get(
            f"/v1/lessons/{test_lesson.id}/status",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_lesson.id
        assert data["status"] == "UPLOADED"

    @pytest.mark.asyncio
    async def test_get_lesson_status_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting status of nonexistent lesson fails."""
        response = await client.get(
            "/v1/lessons/nonexistent-id/status",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestLessonProcess:
    """Tests for processing lessons."""

    @pytest.mark.asyncio
    async def test_process_lesson_not_found(self, client: AsyncClient, auth_headers):
        """Test processing nonexistent lesson fails."""
        response = await client.post(
            "/v1/lessons/nonexistent-id/process",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_process_lesson_unauthenticated(
        self, client: AsyncClient, test_lesson
    ):
        """Test processing lesson without auth fails."""
        response = await client.post(f"/v1/lessons/{test_lesson.id}/process")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_process_uploaded_lesson(
        self, client: AsyncClient, auth_headers, test_lesson
    ):
        """Test processing an uploaded lesson starts background task."""
        response = await client.post(
            f"/v1/lessons/{test_lesson.id}/process",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UPLOADED"


class TestLessonUnauthenticated:
    """Tests for lesson endpoints without authentication."""

    @pytest.mark.asyncio
    async def test_list_lessons_unauthenticated(self, client: AsyncClient):
        """Test listing lessons without auth fails."""
        response = await client.get("/v1/lessons")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_lesson_unauthenticated(self, client: AsyncClient):
        """Test creating lesson without auth fails."""
        response = await client.post(
            "/v1/lessons",
            json={"student_id": "test", "lesson_date": "2024-01-15"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_lesson_unauthenticated(self, client: AsyncClient, test_lesson):
        """Test getting lesson without auth fails."""
        response = await client.get(f"/v1/lessons/{test_lesson.id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_lesson_unauthenticated(self, client: AsyncClient):
        """Test uploading to lesson without auth fails."""
        from io import BytesIO
        files = {"audio": ("test.m4a", BytesIO(b"fake"), "audio/mp4")}
        response = await client.post("/v1/lessons/test-id/upload", files=files)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_lesson_status_unauthenticated(
        self, client: AsyncClient, test_lesson
    ):
        """Test getting lesson status without auth fails."""
        response = await client.get(f"/v1/lessons/{test_lesson.id}/status")
        assert response.status_code == 401
