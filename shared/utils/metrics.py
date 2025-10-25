"""Prometheus metrics collection and export utilities."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from functools import wraps
import time
from typing import Callable, Any

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

request_size = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
)

response_size = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
)

# Error metrics
error_count = Counter(
    'errors_total',
    'Total errors by type',
    ['service', 'error_type']
)

# Business metrics
price_updates = Counter(
    'price_updates_total',
    'Total price updates processed',
    ['source', 'coin_id']
)

sentiment_scores_processed = Counter(
    'sentiment_scores_processed_total',
    'Total sentiment scores processed',
    ['coin_id']
)

portfolio_calculations = Counter(
    'portfolio_calculations_total',
    'Total portfolio calculations',
    ['user_id']
)

# System metrics
active_connections = Gauge(
    'active_connections',
    'Active client connections',
    ['service']
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query latency',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_key']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_key']
)

kafka_messages_produced = Counter(
    'kafka_messages_produced_total',
    'Total Kafka messages produced',
    ['topic']
)

kafka_messages_consumed = Counter(
    'kafka_messages_consumed_total',
    'Total Kafka messages consumed',
    ['topic']
)


def track_request_metrics(endpoint: str) -> Callable:
    """
    Decorator to track HTTP request metrics.

    Args:
        endpoint: Endpoint identifier for metrics

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            method = kwargs.get('method', 'GET')

            try:
                result = await func(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = getattr(e, 'status_code', 500)
                raise
            finally:
                duration = time.time() - start_time
                request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            method = kwargs.get('method', 'GET')

            try:
                result = func(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = getattr(e, 'status_code', 500)
                raise
            finally:
                duration = time.time() - start_time
                request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()

        # Return async wrapper for async functions
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x100:
            return async_wrapper
        return sync_wrapper

    return decorator


def get_metrics() -> bytes:
    """
    Generate Prometheus metrics in text format.

    Returns:
        Prometheus metrics output
    """
    return generate_latest()
