"""
Analytics Service schemas with comprehensive validation.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class MovingAverageRequest(BaseModel):
    """Moving average calculation request."""
    coin_id: str = Field(..., min_length=1, max_length=100, description="Coin identifier")
    period: int = Field(default=20, ge=1, le=500, description="Period for MA calculation")
    method: str = Field(
        default="sma",
        pattern="^(sma|ema)$",
        description="Moving average method: SMA or EMA"
    )
    
    @field_validator('coin_id')
    @classmethod
    def validate_coin_id(cls, v: str) -> str:
        """Validate coin ID format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Coin ID can only contain alphanumeric characters')
        return v


class MovingAverageResponse(BaseModel):
    """Moving average response."""
    coin_id: str = Field(..., description="Coin identifier")
    period: int = Field(..., description="MA period")
    method: str = Field(..., pattern="^(sma|ema)$", description="MA method used")
    values: List[Dict[str, Any]] = Field(..., description="MA values with timestamps")
    timestamp: datetime = Field(..., description="Calculation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class VolatilityRequest(BaseModel):
    """Volatility calculation request."""
    coin_id: str = Field(..., min_length=1, max_length=100, description="Coin identifier")
    period: int = Field(default=20, ge=1, le=500, description="Period for volatility")
    
    @field_validator('coin_id')
    @classmethod
    def validate_coin_id(cls, v: str) -> str:
        """Validate coin ID format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Coin ID can only contain alphanumeric characters')
        return v


class VolatilityResponse(BaseModel):
    """Volatility response."""
    coin_id: str = Field(..., description="Coin identifier")
    period: int = Field(..., description="Volatility period")
    volatility: float = Field(..., ge=0, description="Standard deviation")
    annual_volatility: float = Field(..., ge=0, description="Annualized volatility")
    timestamp: datetime = Field(..., description="Calculation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class CorrelationRequest(BaseModel):
    """Correlation calculation request."""
    coin_id_1: str = Field(..., alias="coin1", description="First coin ID")
    coin_id_2: str = Field(..., alias="coin2", description="Second coin ID")
    period: int = Field(default=30, ge=1, le=500, description="Correlation period")
    
    @field_validator('coin_id_1', 'coin_id_2')
    @classmethod
    def validate_coin_id(cls, v: str) -> str:
        """Validate coin ID format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Coin ID can only contain alphanumeric characters')
        return v


class CorrelationResponse(BaseModel):
    """Correlation response."""
    coin_id_1: str = Field(..., description="First coin ID")
    coin_id_2: str = Field(..., description="Second coin ID")
    period: int = Field(..., description="Correlation period")
    correlation: float = Field(..., ge=-1, le=1, description="Correlation coefficient")
    interpretation: str = Field(..., description="Correlation interpretation")
    timestamp: datetime = Field(..., description="Calculation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class AnalyticsMetricsResponse(BaseModel):
    """Combined analytics metrics response."""
    coin_id: str = Field(..., description="Coin identifier")
    price: float = Field(..., gt=0, description="Current price")
    sma_20: Optional[float] = Field(None, description="20-period SMA")
    ema_20: Optional[float] = Field(None, description="20-period EMA")
    volatility_20: Optional[float] = Field(None, description="20-period volatility")
    volume: Optional[float] = Field(None, description="Trading volume")
    timestamp: datetime = Field(..., description="Metrics timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Service health response."""
    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    service: str = Field(...)
    version: str = Field(...)
    timestamp: datetime = Field(...)
