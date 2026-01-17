"""Authentication endpoint tests."""

import pytest
from httpx import AsyncClient
from app.auth import create_access_token


class TestAuthRegistration:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, db_session):
        """Test successful user registration."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email fails."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "testuser@example.com",
                "password": "password123",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient, db_session):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "full_name": "Invalid Email User",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient, db_session):
        """Test registration with missing fields fails."""
        response = await client.post(
            "/v1/auth/register",
            json={"email": "missing@example.com"},
        )
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password fails."""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient, db_session):
        """Test login with nonexistent email fails."""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "anypassword",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_password(self, client: AsyncClient, db_session):
        """Test login without password fails."""
        response = await client.post(
            "/v1/auth/login",
            json={"email": "testuser@example.com"},
        )
        assert response.status_code == 422


class TestAuthMe:
    """Tests for current user endpoint."""

    @pytest.mark.asyncio
    async def test_me_authenticated(self, client: AsyncClient, auth_headers):
        """Test getting current user when authenticated."""
        response = await client.get("/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["full_name"] == "Test User"
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient, db_session):
        """Test getting current user without auth fails."""
        response = await client.get("/v1/auth/me")
        # FastAPI returns 401 for missing credentials, not 403
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, client: AsyncClient, db_session):
        """Test getting current user with invalid token fails."""
        response = await client.get(
            "/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_token_missing_sub(self, client: AsyncClient, db_session):
        """Test token with missing sub field fails."""
        # Create a token without sub field
        token = create_access_token(data={"email": "test@example.com"})
        response = await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_token_missing_email(self, client: AsyncClient, db_session):
        """Test token with missing email field fails."""
        # Create a token without email field
        token = create_access_token(data={"sub": "user-id"})
        response = await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_user_not_found(self, client: AsyncClient, db_session):
        """Test token for non-existent user fails."""
        # Create a valid token for a user that doesn't exist
        token = create_access_token(
            data={"sub": "non-existent-user-id", "email": "ghost@example.com"}
        )
        response = await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_inactive_user(self, client: AsyncClient, db_session):
        """Test inactive user cannot access protected endpoints."""
        from app.models.user import User
        from app.auth import get_password_hash

        # Create an inactive user
        user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Inactive User",
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create token for inactive user
        token = create_access_token(data={"sub": user.id, "email": user.email})
        response = await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
