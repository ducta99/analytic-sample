"""
Tests for User Service.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from user_service.app.main import app
from shared.utils.database import Base, get_db_session
from shared.utils.auth import hash_password
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


# Tests
class TestUserRegistration:
    """Tests for user registration."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user"]["username"] == "testuser"
        assert data["data"]["access_token"]
        assert data["data"]["refresh_token"]
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email."""
        # First registration
        client.post(
            "/api/users/register",
            json={
                "username": "user1",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        
        # Second registration with same email
        response = client.post(
            "/api/users/register",
            json={
                "username": "user2",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 409
    
    def test_register_short_password(self, client):
        """Test registration with short password."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short"
            }
        )
        assert response.status_code == 422


class TestUserLogin:
    """Tests for user login."""
    
    def test_login_success(self, client):
        """Test successful login."""
        # Register first
        client.post(
            "/api/users/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        
        # Login
        response = client.post(
            "/api/users/login",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["access_token"]
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/users/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401


class TestHealth:
    """Tests for health check."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "user-service"
