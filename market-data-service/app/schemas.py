"""
Market Data Service schemas with comprehensive validation.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List


class PriceUpdateSchema(BaseModel):
    """Price update schema."""
    coin_id: str = Field(..., min_length=1, max_length=100, description="Coin identifier")
    price: float = Field(..., gt=0, description="Price must be positive")
    volume: Optional[float] = Field(None, ge=0, description="Trading volume")
    exchange: Optional[str] = Field(None, description="Exchange name")
    timestamp: datetime = Field(..., description="Update timestamp")
    
    @field_validator('coin_id')
    @classmethod
    def validate_coin_id(cls, v: str) -> str:
        """Validate coin ID format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Coin ID can only contain alphanumeric characters, hyphens, and underscores')
        return v


class CurrentPriceResponse(BaseModel):
    """Current price response."""
    coin_id: str = Field(..., description="Coin identifier")
    price: float = Field(..., description="Current price")
    volume: Optional[float] = Field(None, description="Trading volume")
    timestamp: datetime = Field(..., description="Price timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class PriceHistoryResponse(BaseModel):
    """Price history response."""
    coin_id: str = Field(..., description="Coin identifier")
    prices: List[dict] = Field(..., description="List of price points")
    count: int = Field(..., ge=0, description="Number of data points")
    period: Optional[str] = Field(None, description="Time period (e.g., 24h, 7d, 30d)")
    
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Service health response."""
    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    service: str = Field(...)
    version: str = Field(...)
    timestamp: datetime = Field(...)
