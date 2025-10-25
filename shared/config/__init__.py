"""
Cache configuration.
"""


class CacheConfig:
    """Cache TTL and behavior configuration."""
    
    # Price data - updates every 1-2 seconds
    PRICE_TTL = 10  # 10 seconds
    
    # Analytics metrics - computed periodically
    ANALYTICS_TTL = 60  # 1 minute
    
    # Sentiment analysis - hourly/daily updates
    SENTIMENT_TTL = 300  # 5 minutes
    SENTIMENT_TREND_TTL = 600  # 10 minutes
    
    # Portfolio data - less frequent updates
    PORTFOLIO_TTL = 600  # 10 minutes
    PORTFOLIO_PERF_TTL = 300  # 5 minutes
    
    # User data - profile, preferences
    USER_TTL = 900  # 15 minutes
    
    # Session data
    SESSION_TTL = 86400  # 24 hours
    
    # Authentication tokens
    TOKEN_TTL = 3600  # 1 hour (for revocation lists)
    
    # Market data (coin lists, rankings)
    COINS_LIST_TTL = 3600  # 1 hour
    MARKET_RANKING_TTL = 3600  # 1 hour
    
    # News cache
    NEWS_TTL = 1800  # 30 minutes
    
    # Rate limiting
    RATE_LIMIT_TTL = 60  # 1 minute


# Cache key patterns
CACHE_KEYS = {
    "price": "price:{coin_id}",
    "analytics_moving_avg": "analytics:moving_average:{coin_id}:{period}",
    "analytics_volatility": "analytics:volatility:{coin_id}:{period}",
    "analytics_correlation": "analytics:correlation:{coin_1}:{coin_2}:{period}",
    "sentiment": "sentiment:{coin_id}",
    "sentiment_trend": "sentiment_trend:{coin_id}:{period}",
    "portfolio": "portfolio:{user_id}:{portfolio_id}",
    "portfolio_perf": "portfolio_perf:{user_id}:{portfolio_id}",
    "user": "user:{user_id}",
    "session": "session:{session_id}",
    "token_blacklist": "token:{token_hash}",
    "coins_top": "coins:top:{n}",
    "news": "news:{coin_id}:{source}",
    "rate_limit": "rate_limit:{endpoint}:{user_id}",
}

# Cache warming configuration
CACHE_WARMING_CONFIG = {
    "enabled": True,
    "on_startup": True,
    "on_startup_items": [
        "top_100_coins",
        "top_10_prices",
        "top_10_analytics"
    ],
    "scheduled_tasks": [
        {
            "name": "warm_prices",
            "interval_seconds": 300,
            "items": ["top_100_prices"]
        },
        {
            "name": "warm_analytics",
            "interval_seconds": 3600,
            "items": ["top_100_analytics"]
        }
    ]
}

# Eviction policy when Redis memory is full
EVICTION_POLICY = "allkeys-lru"  # Remove least recently used

# Memory limits
REDIS_MAX_MEMORY = 32 * 1024 * 1024 * 1024  # 32 GB
TARGET_OCCUPANCY_PCT = 85  # Target 85% occupancy
