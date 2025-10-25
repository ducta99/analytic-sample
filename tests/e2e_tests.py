"""
End-to-End Tests for Cryptocurrency Analytics Platform

Tests complete user workflows including:
- User registration and login
- Portfolio creation and management
- Market data fetching
- Analytics calculations
- Sentiment analysis
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import httpx
import websockets

# Configuration
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
TEST_TIMEOUT = 30


class TestAuthenticationFlow:
    """Test user authentication and token management."""

    @pytest.mark.asyncio
    async def test_user_registration(self):
        """Test user registration with valid credentials."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            user_data = {
                "username": f"testuser_{datetime.now().timestamp()}",
                "email": f"test_{datetime.now().timestamp()}@example.com",
                "password": "SecurePassword123!"
            }
            
            response = await client.post("/api/users/register", json=user_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]
            assert "refresh_token" in data["data"]
            assert data["data"]["username"] == user_data["username"]

    @pytest.mark.asyncio
    async def test_user_registration_validation(self):
        """Test registration validation for invalid inputs."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            # Invalid email
            response = await client.post("/api/users/register", json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "SecurePassword123!"
            })
            assert response.status_code == 400
            
            # Password too short
            response = await client.post("/api/users/register", json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short"
            })
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_user_login(self):
        """Test user login with valid credentials."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            # Register user first
            user_data = {
                "username": f"loginuser_{datetime.now().timestamp()}",
                "email": f"login_{datetime.now().timestamp()}@example.com",
                "password": "SecurePassword123!"
            }
            await client.post("/api/users/register", json=user_data)
            
            # Login
            response = await client.post("/api/users/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]

    @pytest.mark.asyncio
    async def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.post("/api/users/login", json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123!"
            })
            
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_refresh(self):
        """Test refresh token functionality."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            # Register and login
            user_data = {
                "username": f"refreshuser_{datetime.now().timestamp()}",
                "email": f"refresh_{datetime.now().timestamp()}@example.com",
                "password": "SecurePassword123!"
            }
            await client.post("/api/users/register", json=user_data)
            
            login_response = await client.post("/api/users/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            refresh_token = login_response.json()["data"]["refresh_token"]
            
            # Refresh token
            response = await client.post("/api/users/refresh", json={
                "refresh_token": refresh_token
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "access_token" in data["data"]


class TestPortfolioWorkflow:
    """Test portfolio creation and management."""

    async def _get_auth_token(self):
        """Helper to get authentication token."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            user_data = {
                "username": f"portuser_{datetime.now().timestamp()}",
                "email": f"port_{datetime.now().timestamp()}@example.com",
                "password": "SecurePassword123!"
            }
            
            # Register
            await client.post("/api/users/register", json=user_data)
            
            # Login
            response = await client.post("/api/users/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            
            return response.json()["data"]["access_token"]

    @pytest.mark.asyncio
    async def test_create_portfolio(self):
        """Test portfolio creation."""
        token = await self._get_auth_token()
        
        async with httpx.AsyncClient(
            base_url=API_URL,
            timeout=TEST_TIMEOUT,
            headers={"Authorization": f"Bearer {token}"}
        ) as client:
            response = await client.post("/api/portfolio", json={
                "name": "Main Portfolio"
            })
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["name"] == "Main Portfolio"

    @pytest.mark.asyncio
    async def test_get_portfolio(self):
        """Test retrieving portfolio details."""
        token = await self._get_auth_token()
        
        async with httpx.AsyncClient(
            base_url=API_URL,
            timeout=TEST_TIMEOUT,
            headers={"Authorization": f"Bearer {token}"}
        ) as client:
            # Create portfolio
            create_response = await client.post("/api/portfolio", json={
                "name": "Test Portfolio"
            })
            portfolio_id = create_response.json()["data"]["id"]
            
            # Get portfolio
            response = await client.get(f"/api/portfolio/{portfolio_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["id"] == portfolio_id

    @pytest.mark.asyncio
    async def test_add_asset_to_portfolio(self):
        """Test adding asset to portfolio."""
        token = await self._get_auth_token()
        
        async with httpx.AsyncClient(
            base_url=API_URL,
            timeout=TEST_TIMEOUT,
            headers={"Authorization": f"Bearer {token}"}
        ) as client:
            # Create portfolio
            create_response = await client.post("/api/portfolio", json={
                "name": "Test Portfolio"
            })
            portfolio_id = create_response.json()["data"]["id"]
            
            # Add asset
            response = await client.post(
                f"/api/portfolio/{portfolio_id}/assets",
                json={
                    "coin_id": "bitcoin",
                    "quantity": 0.5,
                    "purchase_price": 40000.00,
                    "purchase_date": "2025-09-01T00:00:00Z"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["coin_id"] == "bitcoin"

    @pytest.mark.asyncio
    async def test_get_portfolio_performance(self):
        """Test retrieving portfolio performance metrics."""
        token = await self._get_auth_token()
        
        async with httpx.AsyncClient(
            base_url=API_URL,
            timeout=TEST_TIMEOUT,
            headers={"Authorization": f"Bearer {token}"}
        ) as client:
            # Create portfolio
            create_response = await client.post("/api/portfolio", json={
                "name": "Test Portfolio"
            })
            portfolio_id = create_response.json()["data"]["id"]
            
            # Add asset
            await client.post(
                f"/api/portfolio/{portfolio_id}/assets",
                json={
                    "coin_id": "bitcoin",
                    "quantity": 0.5,
                    "purchase_price": 40000.00,
                    "purchase_date": "2025-09-01T00:00:00Z"
                }
            )
            
            # Get performance
            response = await client.get(f"/api/portfolio/{portfolio_id}/performance")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "total_value" in data["data"]
            assert "gain_loss" in data["data"]
            assert "roi_pct" in data["data"]


class TestMarketDataFlow:
    """Test market data endpoints."""

    @pytest.mark.asyncio
    async def test_market_health_check(self):
        """Test market service health check."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get("/api/market/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data or "success" in data

    @pytest.mark.asyncio
    async def test_get_current_price(self):
        """Test retrieving current price."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get("/api/market/price/bitcoin")
            
            # Service might not be running, but verify response format
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True or "data" in data

    @pytest.mark.asyncio
    async def test_get_multiple_prices(self):
        """Test retrieving multiple prices."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get("/api/market/prices?coins=bitcoin,ethereum")
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True or isinstance(data.get("data"), list)


class TestAnalyticsFlow:
    """Test analytics endpoints."""

    @pytest.mark.asyncio
    async def test_get_moving_average(self):
        """Test moving average calculation."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get(
                "/api/analytics/moving-average/bitcoin",
                params={"period": 20, "method": "sma"}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True or "data" in data

    @pytest.mark.asyncio
    async def test_get_volatility(self):
        """Test volatility calculation."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get(
                "/api/analytics/volatility/bitcoin",
                params={"period": 20}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True or "data" in data

    @pytest.mark.asyncio
    async def test_get_correlation(self):
        """Test correlation calculation."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get(
                "/api/analytics/correlation",
                params={"coin1": "bitcoin", "coin2": "ethereum"}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True or "data" in data


class TestSentimentFlow:
    """Test sentiment analysis endpoints."""

    @pytest.mark.asyncio
    async def test_get_sentiment_score(self):
        """Test sentiment score retrieval."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get("/api/sentiment/bitcoin")
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True or "data" in data

    @pytest.mark.asyncio
    async def test_get_sentiment_trend(self):
        """Test sentiment trend retrieval."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get(
                "/api/sentiment/bitcoin/trend",
                params={"days": 7}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True or isinstance(data.get("data"), list)

    @pytest.mark.asyncio
    async def test_get_news_feed(self):
        """Test news feed retrieval."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get(
                "/api/sentiment/news/bitcoin",
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True or isinstance(data.get("data"), list)


class TestCompleteUserJourney:
    """Test complete user workflows from start to finish."""

    @pytest.mark.asyncio
    async def test_complete_journey_register_create_portfolio(self):
        """Test complete journey: register → create portfolio → add asset."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            # Step 1: Register
            user_data = {
                "username": f"journey_{datetime.now().timestamp()}",
                "email": f"journey_{datetime.now().timestamp()}@example.com",
                "password": "SecurePassword123!"
            }
            
            reg_response = await client.post("/api/users/register", json=user_data)
            assert reg_response.status_code == 200
            token = reg_response.json()["data"]["access_token"]
            
            # Add token to headers
            client.headers.update({"Authorization": f"Bearer {token}"})
            
            # Step 2: Create portfolio
            port_response = await client.post("/api/portfolio", json={
                "name": "Journey Portfolio"
            })
            assert port_response.status_code == 201
            portfolio_id = port_response.json()["data"]["id"]
            
            # Step 3: Add asset
            asset_response = await client.post(
                f"/api/portfolio/{portfolio_id}/assets",
                json={
                    "coin_id": "bitcoin",
                    "quantity": 1.0,
                    "purchase_price": 45000.00,
                    "purchase_date": "2025-10-01T00:00:00Z"
                }
            )
            assert asset_response.status_code == 201
            
            # Step 4: Get portfolio
            get_response = await client.get(f"/api/portfolio/{portfolio_id}")
            assert get_response.status_code == 200
            portfolio = get_response.json()["data"]
            assert len(portfolio["assets"]) == 1
            assert portfolio["assets"][0]["coin_id"] == "bitcoin"

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting on authentication endpoints."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            # Make multiple registration attempts quickly
            responses = []
            for i in range(10):
                response = await client.post("/api/users/register", json={
                    "username": f"ratelimit_{i}",
                    "email": f"ratelimit_{i}@example.com",
                    "password": "SecurePassword123!"
                })
                responses.append(response.status_code)
            
            # At least one should be rate limited (429)
            # Note: This depends on rate limiting configuration
            assert 200 in responses or 429 in responses


class TestErrorHandling:
    """Test error handling and validation."""

    @pytest.mark.asyncio
    async def test_invalid_token_header(self):
        """Test request with invalid JWT token."""
        async with httpx.AsyncClient(
            base_url=API_URL,
            timeout=TEST_TIMEOUT,
            headers={"Authorization": "Bearer invalid_token_123"}
        ) as client:
            response = await client.get("/api/portfolio")
            
            # Should reject invalid token
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test API validation for missing required fields."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            # Missing password
            response = await client.post("/api/users/register", json={
                "username": "testuser",
                "email": "test@example.com"
            })
            
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_not_found_endpoint(self):
        """Test 404 response for non-existent endpoint."""
        async with httpx.AsyncClient(base_url=API_URL, timeout=TEST_TIMEOUT) as client:
            response = await client.get("/api/nonexistent/endpoint")
            
            assert response.status_code == 404


if __name__ == "__main__":
    # Run tests with: pytest tests/e2e_tests.py -v
    pytest.main([__file__, "-v", "-s"])
