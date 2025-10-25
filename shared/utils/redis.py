"""
Redis connection pool and utilities.
"""
import logging
from typing import Optional
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError

from shared.utils.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client with connection pooling and retry logic."""
    
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self) -> redis.Redis:
        """Connect to Redis with retry logic.
        
        Returns:
            Redis async client
        """
        if self._client:
            return self._client
        
        try:
            retry = Retry(
                on_error=Retry.DEFAULT_BACKOFF,
                backoff=ExponentialBackoff()
            )
            
            connection_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,
                retry=retry,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            self._client = redis.Redis(connection_pool=connection_pool)
            
            # Test connection
            await self._client.ping()
            logger.info(f"Connected to Redis: {settings.REDIS_URL}")
            
            return self._client
        
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            try:
                await self._client.close()
                self._client = None
                logger.info("Disconnected from Redis")
            except Exception as e:
                logger.error(f"Error disconnecting from Redis: {e}")
    
    @staticmethod
    async def get_client() -> redis.Redis:
        """Get or create Redis client.
        
        Returns:
            Redis async client
        """
        client = RedisClient()
        return await client.connect()


async def get_redis() -> redis.Redis:
    """Get Redis client for dependency injection.
    
    Returns:
        Redis async client
    """
    return await RedisClient.get_client()


async def init_redis() -> None:
    """Initialize Redis connection."""
    try:
        await RedisClient.get_client()
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


async def close_redis() -> None:
    """Close Redis connection."""
    client = RedisClient()
    await client.disconnect()
