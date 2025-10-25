"""
Sentiment storage operations - PostgreSQL and Redis.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import redis.asyncio as redis

from app.models import SentimentScore, NewsArticle

logger = logging.getLogger(__name__)


class SentimentStore:
    """Store sentiment data in PostgreSQL and cache in Redis."""
    
    def __init__(self, db_session: AsyncSession, redis_client: Optional[redis.Redis] = None):
        """Initialize sentiment store.
        
        Args:
            db_session: SQLAlchemy async session
            redis_client: Redis async client for caching
        """
        self.db = db_session
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes
    
    async def save_sentiment(
        self,
        coin_id: str,
        sentiment_score: float,
        positive_pct: float,
        negative_pct: float,
        neutral_pct: float,
        label: str,
        source: str = "news",
        article_count: int = 0
    ) -> SentimentScore:
        """Save sentiment score to database and cache.
        
        Args:
            coin_id: Cryptocurrency ID
            sentiment_score: Score from -1 to +1
            positive_pct: Positive percentage
            negative_pct: Negative percentage
            neutral_pct: Neutral percentage
            label: Sentiment label
            source: Data source
            article_count: Number of articles analyzed
        
        Returns:
            Created SentimentScore object
        """
        try:
            sentiment = SentimentScore(
                coin_id=coin_id,
                score=sentiment_score,
                positive_pct=positive_pct,
                negative_pct=negative_pct,
                neutral_pct=neutral_pct,
                label=label,
                source=source,
                article_count=article_count
            )
            
            self.db.add(sentiment)
            await self.db.flush()
            await self.db.refresh(sentiment)
            
            # Cache the sentiment
            await self._cache_sentiment(sentiment)
            
            logger.debug(f"Saved sentiment for {coin_id}: score={sentiment_score}")
            return sentiment
        
        except Exception as e:
            logger.error(f"Error saving sentiment: {e}")
            await self.db.rollback()
            raise
    
    async def get_latest_sentiment(self, coin_id: str) -> Optional[SentimentScore]:
        """Get latest sentiment score for a coin.
        
        Args:
            coin_id: Cryptocurrency ID
        
        Returns:
            Latest SentimentScore or None
        """
        # Try cache first
        cached = await self._get_cached_sentiment(coin_id)
        if cached:
            return cached
        
        try:
            # Query database for latest
            stmt = select(SentimentScore).where(
                SentimentScore.coin_id == coin_id
            ).order_by(desc(SentimentScore.timestamp)).limit(1)
            
            result = await self.db.execute(stmt)
            sentiment = result.scalar_one_or_none()
            
            if sentiment:
                # Cache for future requests
                await self._cache_sentiment(sentiment)
            
            return sentiment
        
        except Exception as e:
            logger.error(f"Error getting sentiment for {coin_id}: {e}")
            return None
    
    async def get_sentiment_trend(
        self,
        coin_id: str,
        hours: int = 24
    ) -> List[SentimentScore]:
        """Get sentiment trend over a period.
        
        Args:
            coin_id: Cryptocurrency ID
            hours: Look-back period in hours
        
        Returns:
            List of SentimentScore objects ordered by timestamp
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            stmt = select(SentimentScore).where(
                SentimentScore.coin_id == coin_id,
                SentimentScore.timestamp >= since
            ).order_by(SentimentScore.timestamp)
            
            result = await self.db.execute(stmt)
            sentiments = result.scalars().all()
            
            return list(sentiments)
        
        except Exception as e:
            logger.error(f"Error getting sentiment trend for {coin_id}: {e}")
            return []
    
    async def save_article(
        self,
        coin_id: str,
        title: str,
        description: Optional[str],
        url: str,
        source_name: str,
        published_at: datetime,
        content: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> NewsArticle:
        """Save news article to database.
        
        Args:
            coin_id: Associated cryptocurrency
            title: Article title
            description: Brief description
            url: Article URL (must be unique)
            source_name: News source
            published_at: Publication timestamp
            content: Full article content
            image_url: Article image URL
        
        Returns:
            Created NewsArticle object
        """
        try:
            article = NewsArticle(
                coin_id=coin_id,
                title=title,
                description=description,
                url=url,
                source_name=source_name,
                published_at=published_at,
                content=content,
                image_url=image_url
            )
            
            self.db.add(article)
            await self.db.flush()
            await self.db.refresh(article)
            
            logger.debug(f"Saved article: {title[:50]}... for {coin_id}")
            return article
        
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            await self.db.rollback()
            raise
    
    async def get_recent_articles(
        self,
        coin_id: str,
        limit: int = 10
    ) -> List[NewsArticle]:
        """Get recent articles for a coin.
        
        Args:
            coin_id: Cryptocurrency ID
            limit: Maximum number of articles
        
        Returns:
            List of NewsArticle objects
        """
        try:
            stmt = select(NewsArticle).where(
                NewsArticle.coin_id == coin_id
            ).order_by(desc(NewsArticle.published_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        
        except Exception as e:
            logger.error(f"Error getting articles for {coin_id}: {e}")
            return []
    
    async def _cache_sentiment(self, sentiment: SentimentScore) -> bool:
        """Cache sentiment in Redis.
        
        Args:
            sentiment: SentimentScore to cache
        
        Returns:
            True if cached successfully
        """
        if not self.redis:
            return False
        
        try:
            key = f"sentiment:{sentiment.coin_id}"
            value = json.dumps({
                "id": sentiment.id,
                "coin_id": sentiment.coin_id,
                "score": sentiment.score,
                "positive_pct": sentiment.positive_pct,
                "negative_pct": sentiment.negative_pct,
                "neutral_pct": sentiment.neutral_pct,
                "label": sentiment.label,
                "source": sentiment.source,
                "article_count": sentiment.article_count,
                "timestamp": sentiment.timestamp.isoformat()
            })
            
            await self.redis.setex(key, self.cache_ttl, value)
            return True
        
        except Exception as e:
            logger.error(f"Error caching sentiment: {e}")
            return False
    
    async def _get_cached_sentiment(self, coin_id: str) -> Optional[SentimentScore]:
        """Get cached sentiment from Redis.
        
        Args:
            coin_id: Cryptocurrency ID
        
        Returns:
            Cached SentimentScore or None
        """
        if not self.redis:
            return None
        
        try:
            key = f"sentiment:{coin_id}"
            cached = await self.redis.get(key)
            
            if cached:
                data = json.loads(cached)
                # Return as object (simplified for now)
                return data
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting cached sentiment: {e}")
            return None
    
    async def invalidate_sentiment_cache(self, coin_id: str) -> bool:
        """Invalidate cached sentiment.
        
        Args:
            coin_id: Cryptocurrency ID
        
        Returns:
            True if invalidated
        """
        if not self.redis:
            return False
        
        try:
            key = f"sentiment:{coin_id}"
            await self.redis.delete(key)
            return True
        
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
