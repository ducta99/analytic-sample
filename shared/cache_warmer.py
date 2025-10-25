"""
Cache warming service for pre-populating Redis with frequently accessed data.

This service runs scheduled tasks to warm the cache with:
- Popular cryptocurrency prices
- Technical analysis indicators
- Sentiment scores
- Market aggregated data

This reduces latency for frequently accessed endpoints and reduces
database load during peak hours.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import aioredis
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import settings
from shared.models import Price, SentimentScore, AnalyticsMetric
from shared.utils.logging_config import get_logger

logger = get_logger(__name__)

# Cache TTL (Time To Live) in seconds
CACHE_TTLS = {
    "prices": 60,  # 1 minute
    "analytics": 300,  # 5 minutes
    "sentiment": 600,  # 10 minutes
    "market_summary": 300,  # 5 minutes
    "trending_coins": 600,  # 10 minutes
}

# Popular coins to warm cache for
POPULAR_COINS = [
    "bitcoin",
    "ethereum",
    "binance-coin",
    "cardano",
    "solana",
    "polkadot",
    "litecoin",
    "ripple",
    "dogecoin",
    "avalanche-2",
]


class CacheWarmer:
    """Service to warm Redis cache with frequently accessed data."""

    def __init__(self, redis_url: str):
        """Initialize cache warmer.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Establish connections to Redis."""
        try:
            self.redis = await aioredis.create_redis_pool(
                self.redis_url,
                encoding="utf8",
                minsize=5,
                maxsize=10,
            )
            self.http_client = httpx.AsyncClient(timeout=30.0)
            logger.info("Cache warmer connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connections."""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
        if self.http_client:
            await self.http_client.aclose()
        logger.info("Cache warmer disconnected")

    async def warm_prices(
        self, db_session: AsyncSession, coins: Optional[List[str]] = None
    ) -> int:
        """Warm cache with recent price data for popular coins.
        
        Args:
            db_session: Database session
            coins: List of coin IDs to warm (defaults to POPULAR_COINS)
            
        Returns:
            Number of prices cached
        """
        if coins is None:
            coins = POPULAR_COINS

        try:
            cached_count = 0
            
            # Get latest prices from database
            stmt = select(Price).where(Price.coin_id.in_(coins)).order_by(
                Price.coin_id, Price.timestamp.desc()
            )
            result = await db_session.execute(stmt)
            prices = result.fetchall()

            # Group by coin and get latest
            price_map = {}
            for price in prices:
                if price.coin_id not in price_map:
                    price_map[price.coin_id] = price

            # Cache each price
            for coin_id, price_obj in price_map.items():
                key = f"price:{coin_id}:latest"
                value = {
                    "price": str(price_obj.price),
                    "timestamp": price_obj.timestamp.isoformat(),
                    "change_24h": str(price_obj.change_24h),
                }
                
                await self.redis.setex(
                    key,
                    CACHE_TTLS["prices"],
                    json.dumps(value),
                )
                cached_count += 1

            logger.info(f"Warmed {cached_count} price entries in cache")
            return cached_count

        except Exception as e:
            logger.error(f"Error warming prices cache: {e}")
            return 0

    async def warm_analytics(
        self,
        db_session: AsyncSession,
        coins: Optional[List[str]] = None,
        indicators: Optional[List[str]] = None,
    ) -> int:
        """Warm cache with technical analysis indicators.
        
        Args:
            db_session: Database session
            coins: List of coin IDs to warm
            indicators: List of indicator types (SMA, EMA, MACD, etc)
            
        Returns:
            Number of analytics entries cached
        """
        if coins is None:
            coins = POPULAR_COINS
        if indicators is None:
            indicators = ["SMA", "EMA", "VOLATILITY", "RSI"]

        try:
            cached_count = 0

            # Get latest analytics metrics
            stmt = select(AnalyticsMetric).where(
                (AnalyticsMetric.coin_id.in_(coins))
                & (AnalyticsMetric.metric_type.in_(indicators))
            ).order_by(AnalyticsMetric.coin_id, AnalyticsMetric.timestamp.desc())
            
            result = await db_session.execute(stmt)
            metrics = result.fetchall()

            # Group by coin+metric and get latest
            metric_map = {}
            for metric in metrics:
                key = (metric.coin_id, metric.metric_type)
                if key not in metric_map:
                    metric_map[key] = metric

            # Cache each metric
            for (coin_id, metric_type), metric_obj in metric_map.items():
                cache_key = f"analytics:{coin_id}:{metric_type}:latest"
                value = {
                    "value": str(metric_obj.value),
                    "timestamp": metric_obj.timestamp.isoformat(),
                    "metric_type": metric_type,
                }
                
                await self.redis.setex(
                    cache_key,
                    CACHE_TTLS["analytics"],
                    json.dumps(value),
                )
                cached_count += 1

            logger.info(f"Warmed {cached_count} analytics entries in cache")
            return cached_count

        except Exception as e:
            logger.error(f"Error warming analytics cache: {e}")
            return 0

    async def warm_sentiment(
        self, db_session: AsyncSession, coins: Optional[List[str]] = None
    ) -> int:
        """Warm cache with latest sentiment scores.
        
        Args:
            db_session: Database session
            coins: List of coin IDs to warm
            
        Returns:
            Number of sentiment entries cached
        """
        if coins is None:
            coins = POPULAR_COINS

        try:
            cached_count = 0

            # Get latest sentiment scores
            stmt = (
                select(SentimentScore)
                .where(SentimentScore.coin_id.in_(coins))
                .order_by(SentimentScore.coin_id, SentimentScore.timestamp.desc())
            )
            
            result = await db_session.execute(stmt)
            sentiments = result.fetchall()

            # Group by coin and get latest
            sentiment_map = {}
            for sentiment in sentiments:
                if sentiment.coin_id not in sentiment_map:
                    sentiment_map[sentiment.coin_id] = sentiment

            # Cache each sentiment
            for coin_id, sentiment_obj in sentiment_map.items():
                cache_key = f"sentiment:{coin_id}:latest"
                value = {
                    "score": str(sentiment_obj.score),
                    "magnitude": str(sentiment_obj.magnitude),
                    "timestamp": sentiment_obj.timestamp.isoformat(),
                    "source_count": sentiment_obj.source_count,
                }
                
                await self.redis.setex(
                    cache_key,
                    CACHE_TTLS["sentiment"],
                    json.dumps(value),
                )
                cached_count += 1

            logger.info(f"Warmed {cached_count} sentiment entries in cache")
            return cached_count

        except Exception as e:
            logger.error(f"Error warming sentiment cache: {e}")
            return 0

    async def warm_market_summary(self, db_session: AsyncSession) -> bool:
        """Warm cache with aggregated market summary data.
        
        Args:
            db_session: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get top coins by volume
            stmt = select(Price).order_by(Price.volume_24h.desc()).limit(20)
            result = await db_session.execute(stmt)
            prices = result.fetchall()

            total_market_cap = sum(p.market_cap for p in prices if p.market_cap)
            total_volume = sum(p.volume_24h for p in prices if p.volume_24h)

            market_summary = {
                "total_market_cap": str(total_market_cap),
                "total_volume_24h": str(total_volume),
                "top_gainers": [
                    {
                        "coin_id": p.coin_id,
                        "change_24h": str(p.change_24h),
                    }
                    for p in sorted(
                        prices, key=lambda p: p.change_24h or 0, reverse=True
                    )[:5]
                ],
                "top_losers": [
                    {
                        "coin_id": p.coin_id,
                        "change_24h": str(p.change_24h),
                    }
                    for p in sorted(
                        prices, key=lambda p: p.change_24h or 0
                    )[:5]
                ],
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self.redis.setex(
                "market:summary:global",
                CACHE_TTLS["market_summary"],
                json.dumps(market_summary),
            )

            logger.info("Warmed market summary in cache")
            return True

        except Exception as e:
            logger.error(f"Error warming market summary: {e}")
            return False

    async def warm_trending_coins(self, db_session: AsyncSession) -> int:
        """Warm cache with trending coins (most active in last 24h).
        
        Args:
            db_session: Database session
            
        Returns:
            Number of trending coins cached
        """
        try:
            # Get coins with highest volume change
            stmt = select(Price).where(
                Price.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).order_by(Price.volume_24h.desc()).limit(10)
            
            result = await db_session.execute(stmt)
            trending = result.fetchall()

            trending_list = [
                {
                    "coin_id": t.coin_id,
                    "volume_24h": str(t.volume_24h),
                    "change_24h": str(t.change_24h),
                    "price": str(t.price),
                }
                for t in trending
            ]

            await self.redis.setex(
                "market:trending",
                CACHE_TTLS["trending_coins"],
                json.dumps(trending_list),
            )

            logger.info(f"Warmed {len(trending_list)} trending coins in cache")
            return len(trending_list)

        except Exception as e:
            logger.error(f"Error warming trending coins: {e}")
            return 0

    async def warm_all(self, db_session: AsyncSession) -> dict:
        """Execute all warming operations.
        
        Args:
            db_session: Database session
            
        Returns:
            Dictionary with count of cached items by type
        """
        start_time = datetime.utcnow()
        logger.info("Starting cache warming cycle")

        results = {
            "prices": await self.warm_prices(db_session),
            "analytics": await self.warm_analytics(db_session),
            "sentiment": await self.warm_sentiment(db_session),
            "trending": await self.warm_trending_coins(db_session),
        }

        market_ok = await self.warm_market_summary(db_session)
        results["market_summary"] = 1 if market_ok else 0

        duration = (datetime.utcnow() - start_time).total_seconds()
        total_items = sum(results.values())

        logger.info(
            f"Cache warming completed: {total_items} items in {duration:.2f}s",
            extra={"metrics": results},
        )

        return results


async def run_warming_cycle(
    redis_url: str, db_session: AsyncSession, interval_minutes: int = 5
) -> None:
    """Run cache warming on a schedule.
    
    Args:
        redis_url: Redis connection URL
        db_session: Database session
        interval_minutes: Minutes between warming cycles
    """
    warmer = CacheWarmer(redis_url)
    await warmer.connect()

    try:
        while True:
            try:
                await warmer.warm_all(db_session)
            except Exception as e:
                logger.error(f"Error during cache warming cycle: {e}")

            await asyncio.sleep(interval_minutes * 60)

    except asyncio.CancelledError:
        logger.info("Cache warming cycle cancelled")
    finally:
        await warmer.disconnect()


# For use in FastAPI lifespan
async def start_cache_warmer(
    redis_url: str, db_session: AsyncSession
) -> asyncio.Task:
    """Start cache warmer background task.
    
    Args:
        redis_url: Redis connection URL
        db_session: Database session
        
    Returns:
        Asyncio task handle
    """
    task = asyncio.create_task(run_warming_cycle(redis_url, db_session))
    logger.info("Cache warmer task started")
    return task


import json
