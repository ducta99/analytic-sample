"""
Database models for sentiment service.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Index
from shared.utils.database import Base


class SentimentScore(Base):
    """Sentiment analysis result for a coin."""
    
    __tablename__ = "sentiments"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(String(50), nullable=False, index=True)
    score = Column(Float, nullable=False)  # -1 to +1
    positive_pct = Column(Float, nullable=False)
    negative_pct = Column(Float, nullable=False)
    neutral_pct = Column(Float, nullable=False)
    label = Column(String(10), nullable=False)  # positive, negative, neutral
    source = Column(String(50), nullable=False, default="news")
    article_count = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_coin_timestamp", "coin_id", "timestamp"),
        Index("idx_coin_recent", "coin_id", "timestamp", postgresql_desc=True),
    )
    
    def __repr__(self):
        return (f"<SentimentScore(coin_id='{self.coin_id}', "
                f"score={self.score}, label='{self.label}')>")


class NewsArticle(Base):
    """Stored cryptocurrency news article."""
    
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(String(2000))
    url = Column(String(2000), nullable=False, unique=True)
    source_name = Column(String(100), nullable=False)
    published_at = Column(DateTime, nullable=False, index=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    content = Column(String(5000))
    image_url = Column(String(2000))
    sentiment_score = Column(Float)  # Analyzed sentiment
    sentiment_label = Column(String(10))
    
    __table_args__ = (
        Index("idx_coin_published", "coin_id", "published_at"),
    )
    
    def __repr__(self):
        return f"<NewsArticle(title='{self.title[:50]}...', coin_id='{self.coin_id}')>"
