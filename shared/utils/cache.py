"""
Caching decorator for automatic Redis caching.
"""
import json
import logging
from functools import wraps
from typing import Callable, Any, Optional
from datetime import timedelta
import inspect
import redis.asyncio as redis

logger = logging.getLogger(__name__)


def cache_key(*args, prefix: str = "", sep: str = ":") -> str:
    """Generate cache key from arguments.
    
    Args:
        *args: Arguments to include in key
        prefix: Key prefix
        sep: Separator between key parts
    
    Returns:
        Cache key string
    """
    key_parts = [prefix] if prefix else []
    for arg in args:
        if isinstance(arg, (str, int, float)):
            key_parts.append(str(arg))
        elif isinstance(arg, (list, tuple)):
            key_parts.append(",".join(str(x) for x in arg))
    
    return sep.join(key_parts)


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None,
    serialize_json: bool = True
):
    """Decorator for caching function results in Redis.
    
    Args:
        ttl: Time-to-live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
        key_builder: Custom function to build cache key from arguments
        serialize_json: Whether to serialize result as JSON
    
    Returns:
        Decorated function with caching
    
    Example:
        @cached(ttl=600, key_prefix="user")
        async def get_user(user_id: str):
            return await fetch_user_from_db(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Skip caching if redis not available
            redis_client = kwargs.pop("_redis", None)
            if not redis_client:
                return await func(*args, **kwargs)
            
            # Build cache key
            if key_builder:
                cache_key_str = key_builder(*args, **kwargs)
            else:
                prefix = key_prefix or func.__name__
                cache_key_str = cache_key(*args, prefix=prefix)
            
            try:
                # Try to get from cache
                cached_value = await redis_client.get(cache_key_str)
                if cached_value:
                    if serialize_json:
                        return json.loads(cached_value)
                    return cached_value
                
                logger.debug(f"Cache miss: {cache_key_str}")
            
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            try:
                if serialize_json:
                    value = json.dumps(result, default=str)
                else:
                    value = result
                
                await redis_client.setex(cache_key_str, ttl, value)
                logger.debug(f"Cached: {cache_key_str} (ttl={ttl}s)")
            
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For non-async functions, just call directly
            return func(*args, **kwargs)
        
        # Return appropriate wrapper
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(key_pattern: str):
    """Decorator to invalidate cache after function execution.
    
    Args:
        key_pattern: Cache key or pattern to invalidate
    
    Example:
        @invalidate_cache("user:*")
        async def update_user(user_id: str):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, redis_client: Optional[redis.Redis] = None, **kwargs):
            result = await func(*args, **kwargs)
            
            if redis_client:
                try:
                    if "*" in key_pattern:
                        # Pattern-based deletion
                        cursor = 0
                        while True:
                            cursor, keys = await redis_client.scan(cursor, match=key_pattern)
                            if keys:
                                await redis_client.delete(*keys)
                            if cursor == 0:
                                break
                    else:
                        # Exact key deletion
                        await redis_client.delete(key_pattern)
                    
                    logger.debug(f"Invalidated cache: {key_pattern}")
                
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache: {e}")
            
            return result
        
        return async_wrapper
    
    return decorator


class CacheManager:
    """Manager for cache operations."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize cache manager.
        
        Args:
            redis_client: Redis async client
        """
        self.redis = redis_client
    
    async def get(self, key: str, deserialize: bool = True) -> Any:
        """Get value from cache.
        
        Args:
            key: Cache key
            deserialize: Whether to deserialize JSON
        
        Returns:
            Cached value or None
        """
        try:
            value = await self.redis.get(key)
            if value:
                if deserialize:
                    return json.loads(value)
                return value
            return None
        except Exception as e:
            logger.error(f"Error getting cache {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        serialize: bool = True
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            serialize: Whether to serialize as JSON
        
        Returns:
            True if successful
        """
        try:
            if serialize:
                value = json.dumps(value, default=str)
            
            await self.redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
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
            
            logger.debug(f"Deleted {deleted} keys matching {pattern}")
            return deleted
        
        except Exception as e:
            logger.error(f"Error deleting pattern {pattern}: {e}")
            return 0
    
    async def clear_all(self) -> bool:
        """Clear entire cache (DANGEROUS - use with caution).
        
        Returns:
            True if successful
        """
        try:
            await self.redis.flushdb()
            logger.warning("Cleared entire Redis cache")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
