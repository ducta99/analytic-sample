# Cache Strategy and Keys

## Overview

Redis caching layer with structured key patterns for crypto analytics platform.

## Cache Key Patterns

### Price Data
- **Key**: `price:{coin_id}`
- **TTL**: 5-10 seconds
- **Type**: Current price data from market data service
- **Example**: `price:bitcoin`, `price:ethereum`

### Analytics Metrics
- **Key**: `analytics:{metric_type}:{coin_id}:{period}`
- **TTL**: 1-5 minutes
- **Types**: `moving_average`, `volatility`, `correlation`
- **Periods**: `1h`, `24h`, `7d`, `30d`
- **Examples**:
  - `analytics:moving_average:bitcoin:24h`
  - `analytics:volatility:ethereum:7d`
  - `analytics:correlation:bitcoin:ethereum:24h`

### Sentiment Analysis
- **Key**: `sentiment:{coin_id}`
- **TTL**: 5 minutes
- **Type**: Latest sentiment score for coin
- **Example**: `sentiment:bitcoin`, `sentiment:ethereum`

### Sentiment Trends
- **Key**: `sentiment_trend:{coin_id}:{period}`
- **TTL**: 10 minutes
- **Periods**: `24h`, `7d`, `30d`
- **Example**: `sentiment_trend:bitcoin:24h`

### Portfolio Data
- **Key**: `portfolio:{user_id}:{portfolio_id}`
- **TTL**: 10 minutes
- **Type**: Portfolio composition and metadata
- **Example**: `portfolio:user123:portfolio1`

### Portfolio Performance
- **Key**: `portfolio_perf:{user_id}:{portfolio_id}`
- **TTL**: 5 minutes
- **Type**: Calculated performance metrics
- **Example**: `portfolio_perf:user123:portfolio1`

### User Data
- **Key**: `user:{user_id}`
- **TTL**: 15 minutes
- **Type**: User profile and preferences
- **Example**: `user:user123`

### Authentication Tokens
- **Key**: `token:{token_hash}`
- **TTL**: Token expiry time
- **Type**: Blacklisted/revoked tokens
- **Example**: `token:abc123def456`

### Sessions
- **Key**: `session:{session_id}`
- **TTL**: Session timeout (e.g., 24 hours)
- **Type**: Session data
- **Example**: `session:sess_xyz789`

### Coin Lists
- **Key**: `coins:top:{n}`
- **TTL**: 1 hour
- **Type**: Top N coins by market cap
- **Example**: `coins:top:100`

### News Cache
- **Key**: `news:{coin_id}:{source}`
- **TTL**: 30 minutes
- **Type**: Recent news articles
- **Example**: `news:bitcoin:newsapi`

### Rate Limiting
- **Key**: `rate_limit:{endpoint}:{user_id}`
- **TTL**: Time window (e.g., 60 seconds)
- **Type**: Request count for rate limiting
- **Example**: `rate_limit:/api/trades:user123`

## Cache Invalidation Strategy

### Time-to-Live (TTL) Based
- Automatic expiration after configured TTL
- No explicit invalidation needed
- Suitable for most data (prices, analytics)

### Event-Based Invalidation
- Price updates → Invalidate `price:*` and `analytics:*`
- Sentiment updates → Invalidate `sentiment:*` and `sentiment_trend:*`
- Portfolio changes → Invalidate `portfolio:user_id:*` and `portfolio_perf:user_id:*`

### Manual Invalidation
- Admin operations → Clear specific patterns
- Data corrections → Explicit cache deletion
- Testing → Full cache clear (with caution)

### Pattern-Based Deletion
```python
# Invalidate all analytics for a coin
await cache_manager.delete_pattern("analytics:*:bitcoin:*")

# Invalidate all portfolio data for a user
await cache_manager.delete_pattern("portfolio:user123:*")

# Invalidate all price data
await cache_manager.delete_pattern("price:*")
```

## Cache Warming

### Startup Cache Warming
1. Load top 100 coins by market cap
2. Pre-fetch current prices
3. Pre-calculate key analytics metrics
4. Warm sentiment scores for top coins

### Scheduled Cache Warming
- Every 5 minutes: Refresh top coin prices
- Every 1 hour: Refresh analytics metrics
- Every 6 hours: Refresh market rankings

## Memory Management

### Memory Limits
- Redis max memory: 32 GB
- Eviction policy: `allkeys-lru` (remove least recently used)
- Target occupancy: 80-90% of max memory

### Key Expiration
- Monitor average key TTL
- Adjust TTLs based on cache hit rates
- Remove low-value keys to save memory

## Monitoring and Metrics

### Cache Hit/Miss Ratio
- Target: >80% hit rate for price data
- Target: >70% hit rate for analytics
- Target: >60% hit rate for sentiment

### Key Metrics
- Total keys in cache
- Memory usage
- Evictions per second
- Command latency (p50, p95, p99)

## Implementation Examples

### Basic Caching
```python
from shared.utils.cache import cached, CacheManager

@cached(ttl=300, key_prefix="coin")
async def get_coin_info(coin_id: str):
    return await fetch_from_db(coin_id)
```

### Manual Cache Operations
```python
manager = CacheManager(redis_client)

# Get value
sentiment = await manager.get("sentiment:bitcoin")

# Set value
await manager.set("sentiment:bitcoin", {"score": 0.75}, ttl=300)

# Delete single key
await manager.delete("sentiment:bitcoin")

# Delete pattern
await manager.delete_pattern("analytics:*:bitcoin:*")
```

### Cache Invalidation After Updates
```python
from shared.utils.cache import invalidate_cache

@invalidate_cache("price:*")
async def update_price(coin_id: str, price: float):
    await db.update_price(coin_id, price)
```

## Best Practices

1. **Always use TTLs**: No permanent keys except configuration
2. **Be specific with patterns**: Use `analytics:*:bitcoin:*` not just `analytics:*`
3. **Monitor memory**: Keep track of total memory usage
4. **Test invalidation**: Verify cache clears work correctly
5. **Use key prefixes**: Organize keys hierarchically
6. **Avoid large values**: Keep cached values under 1MB
7. **Batch operations**: Use pipeline for multiple operations
8. **Handle failures gracefully**: Cache misses should not crash system
