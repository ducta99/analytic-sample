"""
Cache invalidation strategies.
"""
import logging
from typing import List, Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheInvalidationStrategy:
    """Base class for cache invalidation strategies."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize strategy.
        
        Args:
            redis_client: Redis async client
        """
        self.redis = redis_client
    
    async def invalidate(self, *args, **kwargs) -> bool:
        """Invalidate cache. Must be implemented by subclasses.
        
        Returns:
            True if invalidation successful
        """
        raise NotImplementedError


class TTLBasedInvalidation(CacheInvalidationStrategy):
    """Time-to-live based cache invalidation.
    
    Keys automatically expire after configured TTL.
    No manual invalidation needed.
    """
    
    async def invalidate(self, *args, **kwargs) -> bool:
        """No action needed for TTL-based invalidation.
        
        Returns:
            True (passive strategy)
        """
        return True


class EventBasedInvalidation(CacheInvalidationStrategy):
    """Event-driven cache invalidation.
    
    Triggered by data update events:
    - Price updates → Invalidate price and analytics caches
    - Portfolio changes → Invalidate portfolio caches
    - Sentiment updates → Invalidate sentiment caches
    """
    
    async def invalidate_price_update(self, coin_id: str) -> int:
        """Invalidate caches on price update.
        
        Args:
            coin_id: Cryptocurrency ID
        
        Returns:
            Number of keys deleted
        """
        deleted = 0
        patterns = [
            f"price:{coin_id}",
            f"analytics:*:{coin_id}:*",
            f"portfolio_perf:*:*",  # Affected portfolios
        ]
        
        for pattern in patterns:
            deleted += await self._delete_pattern(pattern)
        
        logger.info(f"Invalidated {deleted} keys for price update: {coin_id}")
        return deleted
    
    async def invalidate_sentiment_update(self, coin_id: str) -> int:
        """Invalidate caches on sentiment update.
        
        Args:
            coin_id: Cryptocurrency ID
        
        Returns:
            Number of keys deleted
        """
        deleted = 0
        patterns = [
            f"sentiment:{coin_id}",
            f"sentiment_trend:{coin_id}:*",
        ]
        
        for pattern in patterns:
            deleted += await self._delete_pattern(pattern)
        
        logger.info(f"Invalidated {deleted} keys for sentiment update: {coin_id}")
        return deleted
    
    async def invalidate_portfolio_update(
        self,
        user_id: str,
        portfolio_id: str
    ) -> int:
        """Invalidate caches on portfolio update.
        
        Args:
            user_id: User ID
            portfolio_id: Portfolio ID
        
        Returns:
            Number of keys deleted
        """
        deleted = 0
        patterns = [
            f"portfolio:{user_id}:{portfolio_id}",
            f"portfolio_perf:{user_id}:{portfolio_id}",
        ]
        
        for pattern in patterns:
            deleted += await self._delete_pattern(pattern)
        
        logger.info(
            f"Invalidated {deleted} keys for portfolio update: "
            f"{user_id}/{portfolio_id}"
        )
        return deleted
    
    async def invalidate_user_update(self, user_id: str) -> int:
        """Invalidate caches on user update.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of keys deleted
        """
        deleted = 0
        patterns = [
            f"user:{user_id}",
            f"portfolio:{user_id}:*",
            f"portfolio_perf:{user_id}:*",
            f"session:*user_id={user_id}*",
        ]
        
        for pattern in patterns:
            deleted += await self._delete_pattern(pattern)
        
        logger.info(f"Invalidated {deleted} keys for user update: {user_id}")
        return deleted
    
    async def _delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
        
        Returns:
            Number of keys deleted
        """
        try:
            deleted = 0
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                if keys:
                    deleted += await self.redis.delete(*keys)
                
                if cursor == 0:
                    break
            
            return deleted
        
        except Exception as e:
            logger.error(f"Error deleting pattern {pattern}: {e}")
            return 0
    
    async def invalidate(self, event_type: str, **kwargs) -> int:
        """Invalidate based on event type.
        
        Args:
            event_type: Type of event (price_update, sentiment_update, etc)
            **kwargs: Event-specific arguments
        
        Returns:
            Number of keys deleted
        """
        if event_type == "price_update":
            return await self.invalidate_price_update(kwargs.get("coin_id"))
        elif event_type == "sentiment_update":
            return await self.invalidate_sentiment_update(kwargs.get("coin_id"))
        elif event_type == "portfolio_update":
            return await self.invalidate_portfolio_update(
                kwargs.get("user_id"),
                kwargs.get("portfolio_id")
            )
        elif event_type == "user_update":
            return await self.invalidate_user_update(kwargs.get("user_id"))
        
        logger.warning(f"Unknown event type: {event_type}")
        return 0


class ManualInvalidation(CacheInvalidationStrategy):
    """Manual cache invalidation.
    
    Explicit invalidation for:
    - Admin operations
    - Data corrections
    - Testing/debugging
    """
    
    async def invalidate(self, key: str) -> bool:
        """Delete specific cache key.
        
        Args:
            key: Exact cache key to delete
        
        Returns:
            True if deleted
        """
        try:
            result = await self.redis.delete(key)
            if result:
                logger.info(f"Invalidated key: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error invalidating key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
        
        Returns:
            Number of keys deleted
        """
        try:
            deleted = 0
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                if keys:
                    deleted += await self.redis.delete(*keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Invalidated {deleted} keys matching: {pattern}")
            return deleted
        
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0
    
    async def invalidate_coin_caches(self, coin_id: str) -> int:
        """Invalidate all caches for a coin.
        
        Args:
            coin_id: Cryptocurrency ID
        
        Returns:
            Number of keys deleted
        """
        deleted = 0
        patterns = [
            f"price:{coin_id}",
            f"analytics:*:{coin_id}:*",
            f"sentiment:{coin_id}",
            f"sentiment_trend:{coin_id}:*",
            f"news:{coin_id}:*",
        ]
        
        for pattern in patterns:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                if keys:
                    deleted += await self.redis.delete(*keys)
                if cursor == 0:
                    break
        
        logger.info(f"Invalidated {deleted} caches for coin: {coin_id}")
        return deleted
    
    async def invalidate_user_caches(self, user_id: str) -> int:
        """Invalidate all caches for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of keys deleted
        """
        deleted = 0
        patterns = [
            f"user:{user_id}",
            f"portfolio:{user_id}:*",
            f"portfolio_perf:{user_id}:*",
        ]
        
        for pattern in patterns:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                if keys:
                    deleted += await self.redis.delete(*keys)
                if cursor == 0:
                    break
        
        logger.info(f"Invalidated {deleted} caches for user: {user_id}")
        return deleted
    
    async def clear_all_caches(self) -> bool:
        """Clear entire Redis cache (DANGEROUS).
        
        Returns:
            True if successful
        """
        try:
            await self.redis.flushdb()
            logger.warning("Cleared ALL caches - this is a dangerous operation")
            return True
        except Exception as e:
            logger.error(f"Error clearing all caches: {e}")
            return False


class CacheInvalidationManager:
    """Manager coordinating all cache invalidation strategies."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize manager.
        
        Args:
            redis_client: Redis async client
        """
        self.redis = redis_client
        self.ttl_strategy = TTLBasedInvalidation(redis_client)
        self.event_strategy = EventBasedInvalidation(redis_client)
        self.manual_strategy = ManualInvalidation(redis_client)
    
    async def on_price_update(self, coin_id: str) -> int:
        """Handle price update event.
        
        Args:
            coin_id: Cryptocurrency ID
        
        Returns:
            Number of caches invalidated
        """
        return await self.event_strategy.invalidate_price_update(coin_id)
    
    async def on_sentiment_update(self, coin_id: str) -> int:
        """Handle sentiment update event.
        
        Args:
            coin_id: Cryptocurrency ID
        
        Returns:
            Number of caches invalidated
        """
        return await self.event_strategy.invalidate_sentiment_update(coin_id)
    
    async def on_portfolio_update(
        self,
        user_id: str,
        portfolio_id: str
    ) -> int:
        """Handle portfolio update event.
        
        Args:
            user_id: User ID
            portfolio_id: Portfolio ID
        
        Returns:
            Number of caches invalidated
        """
        return await self.event_strategy.invalidate_portfolio_update(
            user_id, portfolio_id
        )
    
    async def invalidate_key(self, key: str) -> bool:
        """Manually invalidate a specific key.
        
        Args:
            key: Cache key to invalidate
        
        Returns:
            True if successful
        """
        return await self.manual_strategy.invalidate(key)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Manually invalidate keys matching pattern.
        
        Args:
            pattern: Key pattern
        
        Returns:
            Number of keys invalidated
        """
        return await self.manual_strategy.invalidate_pattern(pattern)
    
    async def clear_all(self) -> bool:
        """Clear all caches.
        
        Returns:
            True if successful
        """
        return await self.manual_strategy.clear_all_caches()
