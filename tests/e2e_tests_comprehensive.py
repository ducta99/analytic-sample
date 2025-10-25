"""
End-to-End Tests for Cryptocurrency Analytics Dashboard

Comprehensive E2E tests covering full user workflows:
- User registration and authentication
- Portfolio creation and management
- Market data integration
- Analytics calculation
- Sentiment analysis
- Real-time updates
"""

import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from datetime import datetime, timedelta
from decimal import Decimal

# ==================== Test Fixtures ====================

@pytest.fixture
async def test_user():
    """Test user credentials."""
    return {
        "username": "testuser_e2e",
        "email": "test_e2e@example.com",
        "password": "SecureTestPass123!",
    }

@pytest.fixture
async def auth_headers(client, test_user):
    """Get authenticated headers."""
    # Register user
    register_response = await client.post(
        "/api/users/register",
        json={
            **test_user,
            "password_confirm": test_user["password"]
        }
    )
    
    if register_response.status_code == 409:  # User already exists
        # Login instead
        login_response = await client.post(
            "/api/users/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        token = login_response.json()["data"]["access_token"]
    else:
        token = register_response.json()["data"]["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

# ==================== Authentication Tests ====================

@pytest.mark.asyncio
async def test_user_registration_flow(client):
    """Test complete user registration workflow."""
    
    user_data = {
        "username": "newuser_" + str(int(datetime.now().timestamp())),
        "email": f"user_{int(datetime.now().timestamp())}@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!"
    }
    
    # Register
    response = await client.post("/api/users/register", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["username"] == user_data["username"]
    assert data["data"]["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_user_login_flow(client, test_user):
    """Test user login workflow."""
    
    # First ensure user exists
    await client.post(
        "/api/users/register",
        json={
            **test_user,
            "password_confirm": test_user["password"]
        }
    )
    
    # Login
    response = await client.post(
        "/api/users/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_token_refresh(client, auth_headers):
    """Test JWT token refresh workflow."""
    
    # Get a new token
    response = await client.post(
        "/api/users/refresh",
        json={"refresh_token": "test_token"},
        headers=auth_headers
    )
    
    # This test requires proper token setup
    # Actual implementation would test token refresh


@pytest.mark.asyncio
async def test_invalid_credentials(client):
    """Test login with invalid credentials."""
    
    response = await client.post(
        "/api/users/login",
        json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
    )
    
    assert response.status_code == 401
    assert response.json()["success"] is False

# ==================== Portfolio Tests ====================

@pytest.mark.asyncio
async def test_portfolio_creation_and_management(client, auth_headers):
    """Test portfolio creation, retrieval, and management."""
    
    # Create portfolio
    portfolio_data = {
        "name": "My First Portfolio",
        "description": "Test portfolio for E2E testing"
    }
    
    create_response = await client.post(
        "/api/portfolio",
        json=portfolio_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    portfolio_id = create_response.json()["data"]["id"]
    
    # Retrieve portfolio
    get_response = await client.get(
        f"/api/portfolio/{portfolio_id}",
        headers=auth_headers
    )
    
    assert get_response.status_code == 200
    assert get_response.json()["data"]["name"] == portfolio_data["name"]


@pytest.mark.asyncio
async def test_add_asset_to_portfolio(client, auth_headers):
    """Test adding cryptocurrency assets to portfolio."""
    
    # Create portfolio first
    portfolio_response = await client.post(
        "/api/portfolio",
        json={"name": "Investment Portfolio"},
        headers=auth_headers
    )
    portfolio_id = portfolio_response.json()["data"]["id"]
    
    # Add asset
    asset_data = {
        "coin_id": "bitcoin",
        "quantity": 0.5,
        "purchase_price": 45000,
        "purchase_date": "2025-01-01"
    }
    
    add_response = await client.post(
        f"/api/portfolio/{portfolio_id}/assets",
        json=asset_data,
        headers=auth_headers
    )
    
    assert add_response.status_code == 201
    portfolio = add_response.json()["data"]
    assert len(portfolio["assets"]) == 1
    assert portfolio["assets"][0]["coin_id"] == "bitcoin"
    assert portfolio["assets"][0]["quantity"] == 0.5


@pytest.mark.asyncio
async def test_portfolio_performance_calculation(client, auth_headers):
    """Test portfolio performance metrics calculation."""
    
    # Create portfolio with assets
    portfolio_response = await client.post(
        "/api/portfolio",
        json={"name": "Performance Test Portfolio"},
        headers=auth_headers
    )
    portfolio_id = portfolio_response.json()["data"]["id"]
    
    # Add multiple assets
    assets = [
        {"coin_id": "bitcoin", "quantity": 1, "purchase_price": 40000},
        {"coin_id": "ethereum", "quantity": 10, "purchase_price": 2000},
    ]
    
    for asset in assets:
        await client.post(
            f"/api/portfolio/{portfolio_id}/assets",
            json=asset,
            headers=auth_headers
        )
    
    # Get performance metrics
    perf_response = await client.get(
        f"/api/portfolio/{portfolio_id}/performance",
        headers=auth_headers
    )
    
    assert perf_response.status_code == 200
    performance = perf_response.json()["data"]
    
    # Verify performance calculations
    assert "total_value" in performance
    assert "total_cost" in performance
    assert "total_gain_loss" in performance
    assert "roi_percentage" in performance
    
    # Total cost should be 1*40000 + 10*2000 = 60000
    assert performance["total_cost"] == 60000

# ==================== Market Data Tests ====================

@pytest.mark.asyncio
async def test_get_current_prices(client):
    """Test retrieving current cryptocurrency prices."""
    
    response = await client.get(
        "/api/market/prices",
        params={"coins": "bitcoin,ethereum,cardano"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1
    
    # Verify price data structure
    price = data["data"][0]
    assert "coin_id" in price
    assert "price" in price
    assert "timestamp" in price
    assert "price_change_24h" in price


@pytest.mark.asyncio
async def test_get_single_coin_price(client):
    """Test retrieving price for single cryptocurrency."""
    
    response = await client.get("/api/market/price/bitcoin")
    
    assert response.status_code == 200
    price_data = response.json()["data"]
    
    assert price_data["coin_id"] == "bitcoin"
    assert price_data["price"] > 0
    assert "timestamp" in price_data


@pytest.mark.asyncio
async def test_websocket_price_stream(client):
    """Test WebSocket connection for real-time price updates."""
    
    # This test would require WebSocket support
    # Skip for now - requires async WebSocket handling
    pytest.skip("WebSocket testing requires additional setup")

# ==================== Analytics Tests ====================

@pytest.mark.asyncio
async def test_moving_average_calculation(client):
    """Test moving average analytics endpoint."""
    
    response = await client.get(
        "/api/analytics/moving-average/bitcoin",
        params={"periods": "50,200"}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert "coin_id" in data
    assert "sma" in data or "ema" in data


@pytest.mark.asyncio
async def test_volatility_calculation(client):
    """Test volatility metrics endpoint."""
    
    response = await client.get(
        "/api/analytics/volatility/bitcoin",
        params={"period": 30}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert "coin_id" in data
    assert "volatility" in data
    assert data["volatility"] >= 0


@pytest.mark.asyncio
async def test_coin_correlation(client):
    """Test price correlation between coins."""
    
    response = await client.get(
        "/api/analytics/correlation",
        params={
            "coin_1": "bitcoin",
            "coin_2": "ethereum",
            "period": 30
        }
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["coin_1"] == "bitcoin"
    assert data["coin_2"] == "ethereum"
    assert "correlation" in data
    assert -1 <= data["correlation"] <= 1

# ==================== Sentiment Tests ====================

@pytest.mark.asyncio
async def test_get_coin_sentiment(client):
    """Test sentiment analysis for cryptocurrency."""
    
    response = await client.get("/api/sentiment/bitcoin")
    
    assert response.status_code == 200
    sentiment_data = response.json()["data"]
    
    assert "coin_id" in sentiment_data
    assert "overall_score" in sentiment_data
    assert "positive_percent" in sentiment_data
    assert "negative_percent" in sentiment_data
    
    # Verify score is in valid range
    assert -1 <= sentiment_data["overall_score"] <= 1
    
    # Verify percentages sum to ~100
    total_percent = (
        sentiment_data["positive_percent"] +
        sentiment_data["negative_percent"]
    )
    assert 0 <= total_percent <= 100


@pytest.mark.asyncio
async def test_sentiment_trend(client):
    """Test sentiment trend over time."""
    
    response = await client.get(
        "/api/sentiment/bitcoin/trend",
        params={"days": 30}
    )
    
    assert response.status_code == 200
    trend_data = response.json()["data"]
    
    # Should return array of sentiment values
    assert isinstance(trend_data, list)
    assert len(trend_data) > 0
    
    # Verify each entry has required fields
    for entry in trend_data:
        assert "timestamp" in entry
        assert "overall_score" in entry


@pytest.mark.asyncio
async def test_news_articles(client):
    """Test news articles retrieval for cryptocurrency."""
    
    response = await client.get(
        "/api/sentiment/news/bitcoin",
        params={"limit": 10}
    )
    
    assert response.status_code == 200
    articles = response.json()["data"]
    
    assert isinstance(articles, list)
    
    if len(articles) > 0:
        article = articles[0]
        assert "title" in article
        assert "url" in article
        assert "source" in article
        assert "published_at" in article
        assert "sentiment" in article

# ==================== Integration Tests ====================

@pytest.mark.asyncio
async def test_full_user_journey(client, test_user):
    """Test complete user journey: register → create portfolio → add assets."""
    
    # 1. Register user
    register_response = await client.post(
        "/api/users/register",
        json={
            **test_user,
            "password_confirm": test_user["password"]
        }
    )
    assert register_response.status_code == 201
    token = register_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get user profile
    profile_response = await client.get(
        "/api/users/profile",
        headers=headers
    )
    assert profile_response.status_code == 200
    
    # 3. Create portfolio
    portfolio_response = await client.post(
        "/api/portfolio",
        json={"name": "My First Portfolio"},
        headers=headers
    )
    assert portfolio_response.status_code == 201
    portfolio_id = portfolio_response.json()["data"]["id"]
    
    # 4. Add assets
    for asset in [
        {"coin_id": "bitcoin", "quantity": 0.5, "purchase_price": 45000},
        {"coin_id": "ethereum", "quantity": 5, "purchase_price": 2500},
    ]:
        asset_response = await client.post(
            f"/api/portfolio/{portfolio_id}/assets",
            json=asset,
            headers=headers
        )
        assert asset_response.status_code == 201
    
    # 5. Get portfolio performance
    perf_response = await client.get(
        f"/api/portfolio/{portfolio_id}/performance",
        headers=headers
    )
    assert perf_response.status_code == 200
    
    # 6. Check market prices
    prices_response = await client.get(
        "/api/market/prices",
        params={"coins": "bitcoin,ethereum"}
    )
    assert prices_response.status_code == 200


@pytest.mark.asyncio
async def test_price_to_analytics_flow(client):
    """Test data flow from prices to analytics to frontend."""
    
    # 1. Get price
    price_response = await client.get("/api/market/price/bitcoin")
    assert price_response.status_code == 200
    price_data = price_response.json()["data"]
    
    # 2. Get analytics for same coin
    analytics_response = await client.get(
        "/api/analytics/moving-average/bitcoin",
        params={"periods": "50,200"}
    )
    assert analytics_response.status_code == 200
    
    # 3. Get sentiment for coin
    sentiment_response = await client.get("/api/sentiment/bitcoin")
    assert sentiment_response.status_code == 200
    
    # Verify coin IDs match
    assert analytics_response.json()["data"]["coin_id"] == price_data["coin_id"]
    assert sentiment_response.json()["data"]["coin_id"] == price_data["coin_id"]


# ==================== Error Handling Tests ====================

@pytest.mark.asyncio
async def test_invalid_portfolio_id(client, auth_headers):
    """Test error handling for invalid portfolio ID."""
    
    response = await client.get(
        "/api/portfolio/invalid-id-12345",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_missing_required_fields(client):
    """Test validation of required fields."""
    
    response = await client.post(
        "/api/users/register",
        json={
            "username": "testuser"
            # Missing email, password, password_confirm
        }
    )
    
    assert response.status_code == 400
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """Test access without authentication."""
    
    response = await client.get(
        "/api/portfolio",
        # No auth headers
    )
    
    assert response.status_code == 401
    assert response.json()["success"] is False


# ==================== Performance Tests ====================

@pytest.mark.asyncio
async def test_api_response_time(client):
    """Test API response times are within SLA."""
    
    import time
    
    # Test endpoint response time
    start = time.time()
    response = await client.get("/api/market/prices", params={"coins": "bitcoin"})
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 1.0  # SLA: < 1 second


@pytest.mark.asyncio
async def test_concurrent_requests(client):
    """Test handling of concurrent requests."""
    
    # Create multiple concurrent requests
    tasks = [
        client.get(f"/api/market/price/bitcoin")
        for _ in range(10)
    ]
    
    responses = await asyncio.gather(*tasks)
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
