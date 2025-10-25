"""
Portfolio Service schemas with comprehensive validation.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal


class PortfolioCreateRequest(BaseModel):
    """Create portfolio request."""
    name: str = Field(..., min_length=1, max_length=100, description="Portfolio name")
    description: Optional[str] = Field(None, max_length=500, description="Portfolio description")


class PortfolioUpdateRequest(BaseModel):
    """Update portfolio request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class PortfolioAssetRequest(BaseModel):
    """Add/update portfolio asset request."""
    coin_id: str = Field(..., min_length=1, max_length=100, description="Coin identifier")
    quantity: float = Field(..., gt=0, description="Asset quantity")
    purchase_price: float = Field(..., gt=0, description="Purchase price per unit")
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    
    @field_validator('coin_id')
    @classmethod
    def validate_coin_id(cls, v: str) -> str:
        """Validate coin ID format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Coin ID can only contain alphanumeric characters')
        return v


class PortfolioAssetResponse(BaseModel):
    """Portfolio asset response."""
    id: int = Field(...)
    portfolio_id: int = Field(...)
    coin_id: str = Field(...)
    quantity: float = Field(..., description="Asset quantity")
    purchase_price: float = Field(..., description="Purchase price per unit")
    purchase_date: datetime = Field(...)
    current_price: Optional[float] = Field(None, description="Current market price")
    current_value: Optional[float] = Field(None, description="Current total value")
    gain_loss: Optional[float] = Field(None, description="Unrealized gain/loss")
    gain_loss_percent: Optional[float] = Field(None, description="Unrealized gain/loss %")
    
    model_config = ConfigDict(from_attributes=True)


class PortfolioResponse(BaseModel):
    """Portfolio response."""
    id: int = Field(...)
    user_id: int = Field(...)
    name: str = Field(...)
    description: Optional[str] = Field(None)
    assets: List[PortfolioAssetResponse] = Field(default_factory=list)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    
    model_config = ConfigDict(from_attributes=True)


class PortfolioPerformanceResponse(BaseModel):
    """Portfolio performance metrics."""
    portfolio_id: int = Field(...)
    total_cost: float = Field(..., description="Total investment amount")
    current_value: float = Field(..., description="Current portfolio value")
    gain_loss: float = Field(..., description="Total gain/loss")
    gain_loss_percent: float = Field(..., description="Total gain/loss %")
    roi_percent: float = Field(..., description="Return on investment %")
    best_performer: Optional[Dict[str, Any]] = Field(None, description="Best performing asset")
    worst_performer: Optional[Dict[str, Any]] = Field(None, description="Worst performing asset")
    asset_count: int = Field(..., description="Number of assets")
    timestamp: datetime = Field(...)
    
    model_config = ConfigDict(from_attributes=True)


class PortfolioHistoryResponse(BaseModel):
    """Portfolio history response."""
    portfolio_id: int = Field(...)
    date: datetime = Field(...)
    value: float = Field(...)
    gain_loss: float = Field(...)
    gain_loss_percent: float = Field(...)
    
    model_config = ConfigDict(from_attributes=True)


class WatchlistItemRequest(BaseModel):
    """Add watchlist item request."""
    coin_id: str = Field(..., min_length=1, max_length=100, description="Coin identifier")
    alert_price: Optional[float] = Field(None, gt=0, description="Price alert threshold")
    
    @field_validator('coin_id')
    @classmethod
    def validate_coin_id(cls, v: str) -> str:
        """Validate coin ID format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Coin ID can only contain alphanumeric characters')
        return v


class WatchlistItemResponse(BaseModel):
    """Watchlist item response."""
    id: int = Field(...)
    user_id: int = Field(...)
    coin_id: str = Field(...)
    current_price: Optional[float] = Field(None)
    alert_price: Optional[float] = Field(None)
    added_at: datetime = Field(...)
    
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Service health response."""
    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    service: str = Field(...)
    version: str = Field(...)
    timestamp: datetime = Field(...)
