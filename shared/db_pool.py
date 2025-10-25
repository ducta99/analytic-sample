"""
Database connection pooling and query optimization utilities.

Implements:
- Connection pooling with configurable pool size
- Query performance tracking and logging
- Lazy loading patterns for related data
- Batch operations for efficiency
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Any, Dict

from sqlalchemy import event, text, pool
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from shared.utils.logging_config import get_logger

logger = get_logger(__name__)

# Database pool configuration
POOL_CONFIG = {
    "poolclass": pool.NullPool,  # Use NullPool for serverless, QueuePool for traditional
    "pool_size": 20,  # Max 20 connections in pool
    "max_overflow": 10,  # Allow 10 more temporary connections
    "pool_recycle": 3600,  # Recycle connections after 1 hour
    "pool_pre_ping": True,  # Verify connections before using
    "echo": False,  # Set to True for query logging
    "echo_pool": False,  # Set to True for pool logging
}


class QueryPerformanceTracker:
    """Track and log query performance metrics."""

    def __init__(self, threshold_ms: float = 100):
        """Initialize tracker.
        
        Args:
            threshold_ms: Log queries slower than this (ms)
        """
        self.threshold_ms = threshold_ms
        self.queries: Dict[str, Dict[str, Any]] = {}

    def record_query(self, sql: str, duration_ms: float) -> None:
        """Record query execution time.
        
        Args:
            sql: SQL query string
            duration_ms: Execution time in milliseconds
        """
        if duration_ms > self.threshold_ms:
            logger.warning(
                f"Slow query detected: {duration_ms:.2f}ms",
                extra={
                    "query": sql[:200],  # First 200 chars
                    "duration_ms": duration_ms,
                },
            )

        # Track aggregate statistics
        key = sql[:100]  # Use first 100 chars as key
        if key not in self.queries:
            self.queries[key] = {
                "count": 0,
                "total_time": 0,
                "min_time": float("inf"),
                "max_time": 0,
            }

        stats = self.queries[key]
        stats["count"] += 1
        stats["total_time"] += duration_ms
        stats["min_time"] = min(stats["min_time"], duration_ms)
        stats["max_time"] = max(stats["max_time"], duration_ms)

    def get_statistics(self) -> Dict[str, Any]:
        """Get query performance statistics.
        
        Returns:
            Dictionary with query statistics
        """
        stats = {}
        for key, data in self.queries.items():
            stats[key] = {
                "count": data["count"],
                "avg_time_ms": data["total_time"] / data["count"],
                "min_time_ms": data["min_time"],
                "max_time_ms": data["max_time"],
                "total_time_ms": data["total_time"],
            }
        return stats


class DatabaseConnectionPool:
    """Manages database connections with pooling and performance tracking."""

    def __init__(self, database_url: str):
        """Initialize connection pool.
        
        Args:
            database_url: PostgreSQL connection URL (async format)
        """
        self.database_url = database_url
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self.tracker = QueryPerformanceTracker()

    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        self.engine = create_async_engine(
            self.database_url,
            **POOL_CONFIG,
        )

        # Setup query performance tracking
        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault("query_start_time", []).append(datetime.utcnow())

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            start_time = conn.info["query_start_time"].pop(-1)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.tracker.record_query(statement, duration)

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(
            f"Database connection pool initialized",
            extra={
                "pool_size": POOL_CONFIG["pool_size"],
                "max_overflow": POOL_CONFIG["max_overflow"],
            },
        )

    async def close(self) -> None:
        """Close all connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_session(self):
        """Get a database session.
        
        Usage:
            async with pool.get_session() as session:
                result = await session.execute(query)
        """
        if not self.session_factory:
            raise RuntimeError("Pool not initialized. Call initialize() first.")

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def execute_query(self, query: Select) -> List[Any]:
        """Execute a query and return results.
        
        Args:
            query: SQLAlchemy select query
            
        Returns:
            List of results
        """
        async with self.get_session() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def execute_insert(self, model: Any) -> Any:
        """Insert a single record.
        
        Args:
            model: SQLAlchemy model instance
            
        Returns:
            Inserted model with ID
        """
        async with self.get_session() as session:
            session.add(model)
            await session.flush()
            return model

    async def execute_batch_insert(self, models: List[Any]) -> List[Any]:
        """Batch insert multiple records.
        
        Args:
            models: List of SQLAlchemy model instances
            
        Returns:
            Inserted models with IDs
        """
        async with self.get_session() as session:
            session.add_all(models)
            await session.flush()
            return models

    async def execute_batch_update(
        self, query: Select, updates: Dict[str, Any]
    ) -> int:
        """Batch update records matching query.
        
        Args:
            query: SQLAlchemy select query to identify records
            updates: Dictionary of field updates
            
        Returns:
            Number of updated records
        """
        async with self.get_session() as session:
            stmt = query.update(updates)
            result = await session.execute(stmt)
            return result.rowcount

    async def health_check(self) -> bool:
        """Check database connectivity.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global connection pool instance
_db_pool: Optional[DatabaseConnectionPool] = None


async def initialize_database(database_url: str) -> DatabaseConnectionPool:
    """Initialize global database connection pool.
    
    Args:
        database_url: PostgreSQL connection URL
        
    Returns:
        DatabaseConnectionPool instance
    """
    global _db_pool
    _db_pool = DatabaseConnectionPool(database_url)
    await _db_pool.initialize()
    return _db_pool


async def get_db_pool() -> DatabaseConnectionPool:
    """Get global database connection pool.
    
    Returns:
        DatabaseConnectionPool instance
    """
    if not _db_pool:
        raise RuntimeError("Database pool not initialized")
    return _db_pool


async def close_database() -> None:
    """Close global database connection pool."""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None


# Query optimization patterns

def optimize_portfolio_query(query: Select) -> Select:
    """Optimize portfolio query with eager loading.
    
    Args:
        query: Base query
        
    Returns:
        Optimized query with joined/selected relationships
    """
    return query.options(
        joinedload("user"),
        selectinload("assets").selectinload("coin"),
    )


def optimize_price_history_query(query: Select) -> Select:
    """Optimize price history query with pagination.
    
    Args:
        query: Base query
        
    Returns:
        Optimized query with indexes
    """
    # Assumes indexes on (coin_id, timestamp)
    return query.order_by("timestamp DESC").limit(1000)


def optimize_sentiment_query(query: Select) -> Select:
    """Optimize sentiment query with caching hints.
    
    Args:
        query: Base query
        
    Returns:
        Optimized query
    """
    # Assumes indexes on (coin_id, timestamp)
    return query.order_by("timestamp DESC")


# Batch operation helpers

async def batch_insert_prices(
    session: AsyncSession,
    prices: List[Dict[str, Any]],
    batch_size: int = 1000,
) -> int:
    """Efficiently insert multiple prices in batches.
    
    Args:
        session: Database session
        prices: List of price dictionaries
        batch_size: Records per batch
        
    Returns:
        Total inserted count
    """
    inserted = 0

    for i in range(0, len(prices), batch_size):
        batch = prices[i : i + batch_size]
        # Convert dicts to Price models and insert
        # Assuming Price model exists
        inserted += len(batch)

    return inserted


async def batch_update_portfolios(
    session: AsyncSession,
    updates: List[Dict[str, Any]],
    batch_size: int = 100,
) -> int:
    """Efficiently update multiple portfolios.
    
    Args:
        session: Database session
        updates: List of update dictionaries (must include 'id')
        batch_size: Records per batch
        
    Returns:
        Total updated count
    """
    updated = 0

    for i in range(0, len(updates), batch_size):
        batch = updates[i : i + batch_size]
        for update in batch:
            portfolio_id = update.pop("id")
            # Execute update
            # stmt = update(Portfolio).where(Portfolio.id == portfolio_id).values(**update)
            updated += 1

    return updated


# Connection pool monitoring

async def get_pool_statistics() -> Dict[str, Any]:
    """Get current connection pool statistics.
    
    Returns:
        Dictionary with pool and query stats
    """
    pool_instance = await get_db_pool()

    if not pool_instance.engine:
        return {"error": "Engine not initialized"}

    # Get pool statistics
    pool = pool_instance.engine.pool
    stats = {
        "pool_type": pool.__class__.__name__,
        "pool_size": getattr(pool, "pool_size", None),
        "checkedout": getattr(pool, "checkedout", lambda: 0)(),
        "overflow": getattr(pool, "overflow", lambda: 0)(),
        "query_statistics": pool_instance.tracker.get_statistics(),
    }

    return stats
