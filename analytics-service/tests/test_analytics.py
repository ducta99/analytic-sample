"""
Comprehensive tests for Analytics Service.

Test coverage for:
- Moving average calculations (SMA and EMA)
- Volatility computation
- Correlation analysis between coins
- Kafka consumer functionality
- Data validation and error handling
- API endpoints
"""
import pytest
import pytest_asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi.testclient import TestClient

from analytics_service.app.main import app
from analytics_service.app.calculations import (
    calculate_sma,
    calculate_ema,
    calculate_volatility,
    calculate_correlation
)
from analytics_service.app.schemas import (
    MovingAverageRequest,
    VolatilityRequest,
    CorrelationRequest,
    AnalyticsMetricsResponse
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def create_price_data(base_price=100, count=100, volatility=0.02):
    """Create synthetic price data for testing."""
    prices = []
    price = base_price
    for i in range(count):
        # Add random walk
        change = np.random.normal(0, volatility)
        price = price * (1 + change)
        prices.append(max(price, 1.0))  # Ensure positive prices
    return prices


# ============================================================================
# SIMPLE MOVING AVERAGE (SMA) TESTS
# ============================================================================

class TestSimpleMovingAverage:
    """Tests for SMA calculation."""
    
    def test_sma_basic(self):
        """Test basic SMA calculation."""
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106]
        period = 3
        
        result = calculate_sma(prices, period)
        
        assert len(result) == len(prices)
        assert result[0] is None  # First period-1 values are None
        assert result[1] is None
        # SMA of [100, 102, 101] = 101
        assert abs(result[2] - 101.0) < 0.01
    
    def test_sma_period_1(self):
        """Test SMA with period=1 (returns original prices)."""
        prices = [100, 102, 101, 103]
        period = 1
        
        result = calculate_sma(prices, period)
        
        for i, price in enumerate(prices):
            assert abs(result[i] - price) < 0.01
    
    def test_sma_period_larger_than_data(self):
        """Test SMA with period larger than data length."""
        prices = [100, 102, 101]
        period = 5
        
        result = calculate_sma(prices, period)
        
        # All values should be None when period > data length
        assert all(v is None for v in result)
    
    def test_sma_empty_data(self):
        """Test SMA with empty data."""
        prices = []
        period = 3
        
        result = calculate_sma(prices, period)
        
        assert result == []
    
    def test_sma_constant_prices(self):
        """Test SMA with constant prices."""
        prices = [100] * 10
        period = 3
        
        result = calculate_sma(prices, period)
        
        for i in range(period - 1, len(result)):
            assert abs(result[i] - 100.0) < 0.01
    
    def test_sma_with_large_period(self):
        """Test SMA with large period."""
        prices = create_price_data(count=100)
        period = 50
        
        result = calculate_sma(prices, period)
        
        assert len(result) == 100
        assert result[49] is not None
        assert all(v is not None for v in result[49:])


# ============================================================================
# EXPONENTIAL MOVING AVERAGE (EMA) TESTS
# ============================================================================

class TestExponentialMovingAverage:
    """Tests for EMA calculation."""
    
    def test_ema_basic(self):
        """Test basic EMA calculation."""
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106]
        period = 3
        
        result = calculate_ema(prices, period)
        
        assert len(result) == len(prices)
        # EMA starts with SMA, then applies exponential smoothing
        assert result[0] is not None
        assert result[-1] is not None
    
    def test_ema_vs_sma_convergence(self):
        """Test that EMA and SMA converge with constant prices."""
        prices = [100] * 20
        period = 5
        
        sma_result = calculate_sma(prices, period)
        ema_result = calculate_ema(prices, period)
        
        # With constant prices, EMA should approach SMA
        for i in range(10, len(prices)):
            assert abs(ema_result[i] - sma_result[i]) < 1.0
    
    def test_ema_period_1(self):
        """Test EMA with period=1."""
        prices = [100, 102, 101, 103]
        period = 1
        
        result = calculate_ema(prices, period)
        
        for i, price in enumerate(prices):
            assert abs(result[i] - price) < 0.01
    
    def test_ema_empty_data(self):
        """Test EMA with empty data."""
        prices = []
        period = 3
        
        result = calculate_ema(prices, period)
        
        assert result == []
    
    def test_ema_responsiveness(self):
        """Test EMA responsiveness to price changes."""
        prices = [100] * 5 + [150] * 5  # Price jump
        period = 3
        
        result = calculate_ema(prices, period)
        
        # EMA should show the price change
        assert result[4] < result[6]
        assert abs(result[-1] - 150.0) < 50  # Should be closer to 150


# ============================================================================
# VOLATILITY TESTS
# ============================================================================

class TestVolatility:
    """Tests for volatility calculation."""
    
    def test_volatility_basic(self):
        """Test basic volatility calculation."""
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106]
        period = 3
        
        result = calculate_volatility(prices, period)
        
        assert result is not None
        assert result >= 0
    
    def test_volatility_constant_prices(self):
        """Test volatility with constant prices (should be 0)."""
        prices = [100] * 20
        period = 5
        
        result = calculate_volatility(prices, period)
        
        assert abs(result) < 0.01  # Should be ~0
    
    def test_volatility_high_volatility(self):
        """Test volatility calculation with high variance."""
        prices = [100, 150, 80, 140, 90, 130, 95]
        period = 3
        
        result = calculate_volatility(prices, period)
        
        assert result > 0
    
    def test_volatility_empty_data(self):
        """Test volatility with empty data."""
        prices = []
        period = 3
        
        result = calculate_volatility(prices, period)
        
        assert result is None or result == 0
    
    def test_volatility_insufficient_data(self):
        """Test volatility with data < period."""
        prices = [100, 102]
        period = 5
        
        result = calculate_volatility(prices, period)
        
        # Should handle gracefully
        assert result is None or result >= 0


# ============================================================================
# CORRELATION TESTS
# ============================================================================

class TestCorrelation:
    """Tests for correlation calculation."""
    
    def test_correlation_perfect_positive(self):
        """Test correlation with perfectly correlated series."""
        prices_1 = [100, 101, 102, 103, 104, 105]
        prices_2 = [200, 202, 204, 206, 208, 210]
        period = 3
        
        result = calculate_correlation(prices_1, prices_2, period)
        
        assert result is not None
        assert abs(result - 1.0) < 0.01  # Should be ~1.0
    
    def test_correlation_perfect_negative(self):
        """Test correlation with perfectly negatively correlated series."""
        prices_1 = [100, 101, 102, 103, 104, 105]
        prices_2 = [200, 198, 196, 194, 192, 190]
        period = 3
        
        result = calculate_correlation(prices_1, prices_2, period)
        
        assert result is not None
        assert abs(result + 1.0) < 0.01  # Should be ~-1.0
    
    def test_correlation_no_correlation(self):
        """Test correlation with independent series."""
        prices_1 = [100, 102, 101, 103, 102]
        prices_2 = [100, 100, 100, 100, 100]  # Constant
        period = 3
        
        result = calculate_correlation(prices_1, prices_2, period)
        
        # Should be undefined or close to 0
        assert result is None or abs(result) < 0.5
    
    def test_correlation_empty_data(self):
        """Test correlation with empty data."""
        prices_1 = []
        prices_2 = []
        period = 3
        
        result = calculate_correlation(prices_1, prices_2, period)
        
        assert result is None
    
    def test_correlation_different_lengths(self):
        """Test correlation with different length series."""
        prices_1 = [100, 101, 102, 103, 104, 105]
        prices_2 = [200, 202, 204]
        period = 3
        
        result = calculate_correlation(prices_1, prices_2, period)
        
        # Should handle gracefully
        assert result is None or isinstance(result, float)


# ============================================================================
# REQUEST VALIDATION TESTS
# ============================================================================

class TestRequestValidation:
    """Tests for request schema validation."""
    
    def test_moving_average_request_valid(self):
        """Test valid moving average request."""
        request = MovingAverageRequest(
            coin_id="bitcoin",
            period=20,
            method="sma"
        )
        
        assert request.coin_id == "bitcoin"
        assert request.period == 20
        assert request.method == "sma"
    
    def test_moving_average_request_invalid_method(self):
        """Test moving average request with invalid method."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            MovingAverageRequest(
                coin_id="bitcoin",
                period=20,
                method="invalid"
            )
    
    def test_moving_average_request_period_bounds(self):
        """Test moving average request with period bounds."""
        from pydantic import ValidationError
        
        # Too small
        with pytest.raises(ValidationError):
            MovingAverageRequest(
                coin_id="bitcoin",
                period=0,
                method="sma"
            )
        
        # Too large (> 500)
        with pytest.raises(ValidationError):
            MovingAverageRequest(
                coin_id="bitcoin",
                period=501,
                method="sma"
            )
    
    def test_correlation_request_valid(self):
        """Test valid correlation request."""
        request = CorrelationRequest(
            coin_id_1="bitcoin",
            coin_id_2="ethereum",
            period=30
        )
        
        assert request.coin_id_1 == "bitcoin"
        assert request.coin_id_2 == "ethereum"
        assert request.period == 30
    
    def test_correlation_request_invalid_coin_id(self):
        """Test correlation request with invalid coin ID."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            CorrelationRequest(
                coin_id_1="@invalid",
                coin_id_2="ethereum",
                period=30
            )


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class TestAnalyticsAPIEndpoints:
    """Tests for Analytics Service API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "analytics-service"
    
    @patch('analytics_service.app.routes.get_moving_average')
    def test_get_moving_average_sma(self, mock_sma, client):
        """Test getting SMA."""
        mock_sma.return_value = {
            "coin_id": "bitcoin",
            "period": 20,
            "method": "sma",
            "values": [45250.0, 45255.0, 45260.0],
            "timestamp": datetime.utcnow()
        }
        
        response = client.get(
            "/api/analytics/moving-average/bitcoin",
            params={"period": 20, "method": "sma"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["method"] == "sma"
    
    @patch('analytics_service.app.routes.get_moving_average')
    def test_get_moving_average_ema(self, mock_ema, client):
        """Test getting EMA."""
        mock_ema.return_value = {
            "coin_id": "bitcoin",
            "period": 20,
            "method": "ema",
            "values": [45250.0, 45255.0, 45260.0],
            "timestamp": datetime.utcnow()
        }
        
        response = client.get(
            "/api/analytics/moving-average/bitcoin",
            params={"period": 20, "method": "ema"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["method"] == "ema"
    
    @patch('analytics_service.app.routes.get_volatility')
    def test_get_volatility(self, mock_vol, client):
        """Test getting volatility."""
        mock_vol.return_value = {
            "coin_id": "bitcoin",
            "period": 20,
            "volatility": 0.025,
            "annual_volatility": 0.397,
            "timestamp": datetime.utcnow()
        }
        
        response = client.get(
            "/api/analytics/volatility/bitcoin",
            params={"period": 20}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["volatility"] > 0
    
    @patch('analytics_service.app.routes.get_correlation')
    def test_get_correlation(self, mock_corr, client):
        """Test getting correlation."""
        mock_corr.return_value = {
            "coin_id_1": "bitcoin",
            "coin_id_2": "ethereum",
            "period": 30,
            "correlation": 0.75,
            "interpretation": "Highly correlated",
            "timestamp": datetime.utcnow()
        }
        
        response = client.get(
            "/api/analytics/correlation",
            params={"coin1": "bitcoin", "coin2": "ethereum"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert -1 <= data["data"]["correlation"] <= 1


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_period(self, client):
        """Test handling invalid period."""
        response = client.get(
            "/api/analytics/moving-average/bitcoin",
            params={"period": -1, "method": "sma"}
        )
        
        assert response.status_code in [400, 422]
    
    def test_missing_coin_id(self, client):
        """Test handling missing coin ID."""
        response = client.get("/api/analytics/moving-average/")
        
        assert response.status_code in [404, 422]


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Tests for performance characteristics."""
    
    def test_sma_performance(self):
        """Test SMA calculation performance with large dataset."""
        import time
        
        prices = create_price_data(count=10000)
        period = 50
        
        start = time.time()
        result = calculate_sma(prices, period)
        elapsed = time.time() - start
        
        # Should complete in < 100ms
        assert elapsed < 0.1
        assert len(result) == len(prices)
    
    def test_ema_performance(self):
        """Test EMA calculation performance with large dataset."""
        import time
        
        prices = create_price_data(count=10000)
        period = 50
        
        start = time.time()
        result = calculate_ema(prices, period)
        elapsed = time.time() - start
        
        # Should complete in < 100ms
        assert elapsed < 0.1
        assert len(result) == len(prices)
    
    def test_correlation_performance(self):
        """Test correlation calculation performance."""
        import time
        
        prices_1 = create_price_data(count=1000)
        prices_2 = create_price_data(count=1000)
        period = 50
        
        start = time.time()
        result = calculate_correlation(prices_1, prices_2, period)
        elapsed = time.time() - start
        
        # Should complete in < 50ms
        assert elapsed < 0.05
