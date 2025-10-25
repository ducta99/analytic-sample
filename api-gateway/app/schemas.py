"""
OpenAPI schemas for API Gateway documentation.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== Authentication Schemas ====================

class UserRegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 chars)")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepass123"
            }
        }


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "securepass123"
            }
        }


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str = Field(..., description="Refresh token from login response")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class AuthResponse(BaseModel):
    """Authentication response with tokens."""
    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="Auth data")
    meta: Dict[str, Any] = Field(..., description="Metadata including timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "user_id": 1,
                    "username": "john_doe",
                    "email": "john@example.com",
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_expires_in": 3600
                },
                "meta": {
                    "timestamp": "2025-10-25T10:30:00Z"
                }
            }
        }


# ==================== Market Data Schemas ====================

class PriceUpdate(BaseModel):
    """Price update data."""
    coin_id: str = Field(..., description="Cryptocurrency ID (e.g., 'bitcoin')")
    symbol: str = Field(..., description="Coin symbol (e.g., 'BTC')")
    price: float = Field(..., gt=0, description="Current price in USD")
    volume: Optional[float] = Field(None, description="24h trading volume")
    price_change_pct: Optional[float] = Field(None, description="24h price change percentage")
    timestamp: datetime = Field(..., description="Update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "coin_id": "bitcoin",
                "symbol": "BTC",
                "price": 45250.50,
                "volume": 28500000000,
                "price_change_pct": 2.45,
                "timestamp": "2025-10-25T10:30:15Z"
            }
        }


class PriceResponse(BaseModel):
    """Price query response."""
    success: bool
    data: PriceUpdate
    meta: Dict[str, Any]


class MultiPriceResponse(BaseModel):
    """Multiple prices response."""
    success: bool
    data: List[PriceUpdate]
    meta: Dict[str, Any]


# ==================== Analytics Schemas ====================

class MovingAverageResponse(BaseModel):
    """Moving average calculation response."""
    success: bool = Field(...)
    data: Dict[str, Any] = Field(...)
    meta: Dict[str, Any] = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "coin_id": "bitcoin",
                    "method": "sma",
                    "period": 20,
                    "current_value": 44875.30,
                    "values": [
                        {"timestamp": "2025-10-25T09:00:00Z", "value": 44500.00},
                        {"timestamp": "2025-10-25T09:30:00Z", "value": 44600.50}
                    ]
                },
                "meta": {"timestamp": "2025-10-25T10:30:00Z"}
            }
        }


class VolatilityResponse(BaseModel):
    """Volatility calculation response."""
    success: bool = Field(...)
    data: Dict[str, Any] = Field(...)
    meta: Dict[str, Any] = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "coin_id": "bitcoin",
                    "period": 20,
                    "volatility": 0.0245,
                    "volatility_pct": 2.45,
                    "min_price": 44200.00,
                    "max_price": 46100.00,
                    "avg_price": 45250.50
                },
                "meta": {"timestamp": "2025-10-25T10:30:00Z"}
            }
        }


class CorrelationResponse(BaseModel):
    """Correlation analysis response."""
    success: bool = Field(...)
    data: Dict[str, Any] = Field(...)
    meta: Dict[str, Any] = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "coin_1": "bitcoin",
                    "coin_2": "ethereum",
                    "correlation": 0.85,
                    "period": 30,
                    "interpretation": "Strong positive correlation"
                },
                "meta": {"timestamp": "2025-10-25T10:30:00Z"}
            }
        }


# ==================== Sentiment Schemas ====================

class SentimentScore(BaseModel):
    """Sentiment score."""
    score: float = Field(..., ge=-1, le=1, description="Sentiment score from -1 (negative) to 1 (positive)")
    positive_pct: float = Field(..., ge=0, le=100)
    negative_pct: float = Field(..., ge=0, le=100)
    neutral_pct: float = Field(..., ge=0, le=100)


class SentimentResponse(BaseModel):
    """Sentiment analysis response."""
    success: bool = Field(...)
    data: Dict[str, Any] = Field(...)
    meta: Dict[str, Any] = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "coin_id": "bitcoin",
                    "overall_score": 0.65,
                    "positive_pct": 72,
                    "negative_pct": 18,
                    "neutral_pct": 10,
                    "articles_analyzed": 150,
                    "trend": "improving"
                },
                "meta": {"timestamp": "2025-10-25T10:30:00Z"}
            }
        }


class NewsArticle(BaseModel):
    """News article."""
    id: str
    title: str
    description: Optional[str]
    url: str
    source: str
    published_at: datetime
    sentiment_score: Optional[float]


class NewsResponse(BaseModel):
    """News feed response."""
    success: bool
    data: List[NewsArticle]
    meta: Dict[str, Any]


# ==================== Portfolio Schemas ====================

class PortfolioAsset(BaseModel):
    """Portfolio asset."""
    coin_id: str
    symbol: str
    quantity: float = Field(..., gt=0)
    purchase_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    purchase_date: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "coin_id": "bitcoin",
                "symbol": "BTC",
                "quantity": 0.5,
                "purchase_price": 40000.00,
                "current_price": 45250.50,
                "purchase_date": "2025-09-01T00:00:00Z"
            }
        }


class PortfolioPerformance(BaseModel):
    """Portfolio performance metrics."""
    total_value: float
    total_cost: float
    gain_loss: float
    gain_loss_pct: float
    roi_pct: float


class PortfolioResponse(BaseModel):
    """Portfolio response."""
    success: bool
    data: Dict[str, Any]
    meta: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "portfolio_id": 1,
                    "user_id": 1,
                    "name": "Main Portfolio",
                    "assets": [
                        {
                            "coin_id": "bitcoin",
                            "symbol": "BTC",
                            "quantity": 0.5,
                            "purchase_price": 40000.00,
                            "current_price": 45250.50,
                            "purchase_date": "2025-09-01T00:00:00Z"
                        }
                    ],
                    "performance": {
                        "total_value": 22625.25,
                        "total_cost": 20000.00,
                        "gain_loss": 2625.25,
                        "gain_loss_pct": 13.13,
                        "roi_pct": 13.13
                    },
                    "created_at": "2025-09-01T00:00:00Z"
                },
                "meta": {"timestamp": "2025-10-25T10:30:00Z"}
            }
        }


# ==================== Error Schemas ====================

class ErrorDetail(BaseModel):
    """Error detail."""
    code: str = Field(..., description="Error code (e.g., 'VALIDATION_ERROR')")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = Field(False)
    error: ErrorDetail
    meta: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input parameters",
                    "details": {
                        "email": "Invalid email format"
                    }
                },
                "meta": {"timestamp": "2025-10-25T10:30:00Z"}
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status ('healthy', 'degraded', 'unhealthy')")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime


# ==================== WebSocket Message Schemas ====================

class WebSocketMessageType(str, Enum):
    """WebSocket message types."""
    PRICE_UPDATE = "price_update"
    SENTIMENT_UPDATE = "sentiment_update"
    PORTFOLIO_UPDATE = "portfolio_update"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class WebSocketMessage(BaseModel):
    """WebSocket message."""
    type: WebSocketMessageType
    data: Dict[str, Any]
    timestamp: datetime
    message_id: str = Field(..., description="Unique message ID for deduplication")
