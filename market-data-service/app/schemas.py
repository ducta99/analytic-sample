"""
Market Data Service schemas.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class PriceUpdateSchema(BaseModel):
    """Price update schema."""
    coin_id: str
    price: float
    volume: Optional[float] = None
    exchange: Optional[str] = None
    timestamp: datetime


class CurrentPriceResponse(BaseModel):
    """Current price response."""
    coin_id: str
    price: float
    volume: Optional[float] = None
    timestamp: datetime


class HealthResponse(BaseModel):
    """Service health response."""
    status: str
    service: str
    version: str
    timestamp: datetime
