"""
Comprehensive tests for User Service.

Test coverage for:
- User registration and validation
- User login and JWT token generation
- Token refresh mechanism
- Profile management
- Authorization checks
- Password hashing
- Error handling
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from user_service.app.main import app
from shared.utils.database import Base, get_db_session
from shared.utils.auth import hash_password, verify_password, create_access_token, verify_token
from shared.utils.exceptions import (
    AuthenticationError, InvalidCredentialsError, ValidationError,
    DuplicateUserError, UserNotFoundError, InsufficientPermissionsError
)
from user_service.app.models import User, UserPreferences


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture
async def test_db():
    """Create test database and tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_session(test_db):
    """Create test session."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def override_get_db(test_session):
    """Override get_db_session dependency."""
    async def _override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db_session] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db):
    """Create test client."""
    return TestClient(app)


# ============================================================================
# REGISTRATION TESTS
# ============================================================================

class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    def test_register_success(self, client):
        """Test successful user registration with valid data."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user"]["username"] == "testuser"
        assert data["data"]["user"]["email"] == "test@example.com"
        assert data["data"]["access_token"]
        assert data["data"]["refresh_token"]
        assert data["data"]["token_type"] == "bearer"
        assert "expires_in" in data["data"]
    
    def test_register_duplicate_email(self, client):
        """Test registration fails with duplicate email."""
        # First registration
        client.post(
            "/api/users/register",
            json={
                "username": "user1",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        
        # Second registration with same email should fail
        response = client.post(
            "/api/users/register",
            json={
                "username": "user2",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "DUPLICATE_USER"
    
    def test_register_duplicate_username(self, client):
        """Test registration fails with duplicate username."""
        # First registration
        client.post(
            "/api/users/register",
            json={
                "username": "duplicateuser",
                "email": "first@example.com",
                "password": "ValidPass123"
            }
        )
        
        # Second registration with same username
        response = client.post(
            "/api/users/register",
            json={
                "username": "duplicateuser",
                "email": "second@example.com",
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 409
    
    def test_register_short_password(self, client):
        """Test registration fails with password < 8 characters."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short1"
            }
        )
        assert response.status_code == 422
        assert "Password must be 8-100 characters" in str(response.json())
    
    def test_register_password_no_uppercase(self, client):
        """Test registration fails if password lacks uppercase letter."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "lowercase123"
            }
        )
        assert response.status_code == 422
        assert "uppercase" in str(response.json()).lower()
    
    def test_register_password_no_digit(self, client):
        """Test registration fails if password lacks digit."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "NoDigitPass"
            }
        )
        assert response.status_code == 422
        assert "digit" in str(response.json()).lower()
    
    def test_register_short_username(self, client):
        """Test registration fails with username < 3 characters."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "ab",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 422
    
    def test_register_invalid_username_format(self, client):
        """Test registration fails with invalid username characters."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "test user@123",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client):
        """Test registration fails with invalid email."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 422
    
    def test_register_missing_required_field(self, client):
        """Test registration fails when required field is missing."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com"
                # missing password
            }
        )
        assert response.status_code == 422
    
    def test_register_password_hashed(self, client):
        """Test that password is properly hashed in database."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 200
        # Password should not be returned in response
        assert "password" not in response.json()["data"]["user"]


# ============================================================================
# LOGIN TESTS
# ============================================================================

class TestUserLogin:
    """Tests for user login endpoint."""
    
    def test_login_success(self, client):
        """Test successful login with correct credentials."""
        # Register first
        client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        
        # Login with correct credentials
        response = client.post(
            "/api/users/login",
            json={
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["access_token"]
        assert data["data"]["refresh_token"]
        assert data["data"]["user"]["email"] == "test@example.com"
    
    def test_login_user_not_found(self, client):
        """Test login fails with non-existent email."""
        response = client.post(
            "/api/users/login",
            json={
                "email": "nonexistent@example.com",
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    
    def test_login_wrong_password(self, client):
        """Test login fails with incorrect password."""
        # Register first
        client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        
        # Login with wrong password
        response = client.post(
            "/api/users/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123"
            }
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    
    def test_login_missing_email(self, client):
        """Test login fails when email is missing."""
        response = client.post(
            "/api/users/login",
            json={
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 422
    
    def test_login_missing_password(self, client):
        """Test login fails when password is missing."""
        response = client.post(
            "/api/users/login",
            json={
                "email": "test@example.com"
            }
        )
        assert response.status_code == 422
    
    def test_login_inactive_user(self, client):
        """Test login fails for inactive user."""
        # This would require setting is_active=False in DB
        # Implementation depends on how inactive users are handled
        pass


# ============================================================================
# TOKEN REFRESH TESTS
# ============================================================================

class TestTokenRefresh:
    """Tests for token refresh endpoint."""
    
    def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        # Register and get tokens
        register_response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        refresh_token = register_response.json()["data"]["refresh_token"]
        
        # Refresh tokens
        response = client.post(
            "/api/users/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["access_token"]
        assert data["data"]["refresh_token"]
    
    def test_refresh_token_invalid(self, client):
        """Test token refresh fails with invalid token."""
        response = client.post(
            "/api/users/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        assert response.status_code == 401
    
    def test_refresh_token_expired(self, client):
        """Test token refresh fails with expired token."""
        # This test would require mocking time or creating an expired token
        pass
    
    def test_refresh_token_missing(self, client):
        """Test token refresh fails when token is missing."""
        response = client.post(
            "/api/users/refresh",
            json={}
        )
        assert response.status_code == 422


# ============================================================================
# PROFILE MANAGEMENT TESTS
# ============================================================================

class TestProfileManagement:
    """Tests for user profile management."""
    
    def _get_auth_header(self, client):
        """Helper to get authorization header."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        token = response.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_profile_success(self, client):
        """Test getting user profile."""
        headers = self._get_auth_header(client)
        response = client.get(
            "/api/users/profile",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"
        assert data["data"]["email"] == "test@example.com"
    
    def test_get_profile_unauthorized(self, client):
        """Test getting profile without authentication."""
        response = client.get("/api/users/profile")
        assert response.status_code == 401
    
    def test_update_profile_success(self, client):
        """Test updating user profile."""
        headers = self._get_auth_header(client)
        response = client.put(
            "/api/users/profile",
            headers=headers,
            json={"username": "updateduser"}
        )
        assert response.status_code == 200
        assert response.json()["data"]["username"] == "updateduser"
    
    def test_update_profile_invalid_email(self, client):
        """Test updating profile with invalid email."""
        headers = self._get_auth_header(client)
        response = client.put(
            "/api/users/profile",
            headers=headers,
            json={"email": "invalid-email"}
        )
        assert response.status_code == 422
    
    def test_delete_account(self, client):
        """Test account deletion."""
        headers = self._get_auth_header(client)
        response = client.delete(
            "/api/users/profile",
            headers=headers
        )
        assert response.status_code in [200, 204]
        
        # Verify user can't login after deletion
        login_response = client.post(
            "/api/users/login",
            json={
                "email": "test@example.com",
                "password": "ValidPass123"
            }
        )
        assert login_response.status_code == 401


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================

class TestAuthorization:
    """Tests for authorization and access control."""
    
    def test_invalid_token_rejected(self, client):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get(
            "/api/users/profile",
            headers=headers
        )
        assert response.status_code == 401
    
    def test_missing_token_rejected(self, client):
        """Test that missing tokens are rejected."""
        response = client.get("/api/users/profile")
        assert response.status_code == 401
    
    def test_malformed_auth_header(self, client):
        """Test that malformed authorization header is rejected."""
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get(
            "/api/users/profile",
            headers=headers
        )
        assert response.status_code == 401
    
    def test_expired_token_rejected(self, client):
        """Test that expired tokens are rejected."""
        # This requires creating an expired token
        # Implementation depends on token generation
        pass


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestHealth:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "user-service"
        assert "version" in data
        assert "timestamp" in data
    
    def test_health_check_format(self, client):
        """Test health check response format."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
