"""
Sentiment Service schemas with comprehensive validation.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class ArticleRequest(BaseModel):
    """Article request for sentiment analysis."""
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    content: str = Field(..., min_length=10, max_length=50000, description="Article content")
    source: str = Field(..., min_length=1, max_length=200, description="Article source")
    url: Optional[str] = Field(None, description="Article URL")
    coin_ids: List[str] = Field(..., min_items=1, description="Relevant coin IDs")
    published_at: Optional[datetime] = Field(None, description="Publication date")
    
    @field_validator('coin_ids')
    @classmethod
    def validate_coin_ids(cls, v: List[str]) -> List[str]:
        """Validate coin IDs."""
        for coin_id in v:
            if not coin_id.replace('-', '').replace('_', '').isalnum():
                raise ValueError(f'Invalid coin ID: {coin_id}')
        return v


class SentimentScoreResponse(BaseModel):
    """Sentiment score response."""
    text: str = Field(..., description="Analyzed text")
    score: float = Field(..., ge=-1, le=1, description="Sentiment score (-1 to 1)")
    label: str = Field(..., pattern="^(positive|neutral|negative)$", description="Sentiment label")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    
    model_config = ConfigDict(from_attributes=True)


class ArticleAnalysisResponse(BaseModel):
    """Article analysis response."""
    article_id: int = Field(...)
    title: str = Field(...)
    source: str = Field(...)
    url: Optional[str] = Field(None)
    sentiment: SentimentScoreResponse = Field(...)
    relevant_coins: List[str] = Field(..., description="Coins mentioned in article")
    published_at: datetime = Field(...)
    analyzed_at: datetime = Field(...)
    
    model_config = ConfigDict(from_attributes=True)


class CoinSentimentResponse(BaseModel):
    """Sentiment for a specific coin."""
    coin_id: str = Field(..., description="Coin identifier")
    current_score: float = Field(..., ge=-1, le=1, description="Current sentiment score")
    label: str = Field(..., pattern="^(positive|neutral|negative)$")
    positive_count: int = Field(..., ge=0, description="Number of positive articles")
    neutral_count: int = Field(..., ge=0, description="Number of neutral articles")
    negative_count: int = Field(..., ge=0, description="Number of negative articles")
    total_articles: int = Field(..., ge=0)
    positive_percent: float = Field(..., ge=0, le=100)
    neutral_percent: float = Field(..., ge=0, le=100)
    negative_percent: float = Field(..., ge=0, le=100)
    timestamp: datetime = Field(...)
    
    model_config = ConfigDict(from_attributes=True)


class SentimentTrendResponse(BaseModel):
    """Sentiment trend over time."""
    coin_id: str = Field(..., description="Coin identifier")
    period: str = Field(..., pattern="^(1h|24h|7d|30d)$", description="Time period")
    data_points: List[Dict[str, Any]] = Field(..., description="Trend data points")
    start_score: float = Field(..., ge=-1, le=1)
    end_score: float = Field(..., ge=-1, le=1)
    trend_direction: str = Field(..., pattern="^(up|down|stable)$")
    
    model_config = ConfigDict(from_attributes=True)


class NewsFeedResponse(BaseModel):
    """News feed for a coin."""
    coin_id: str = Field(..., description="Coin identifier")
    articles: List[ArticleAnalysisResponse] = Field(..., description="Articles about the coin")
    total_count: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)
    
    model_config = ConfigDict(from_attributes=True)


class SentimentComparisonResponse(BaseModel):
    """Sentiment comparison between coins."""
    coins: List[Dict[str, Any]] = Field(..., description="Sentiment data for each coin")
    timestamp: datetime = Field(...)
    
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Service health response."""
    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    service: str = Field(...)
    version: str = Field(...)
    timestamp: datetime = Field(...)
