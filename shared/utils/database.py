"""
Shared database utilities and connection management.
"""
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, StaticPool

from shared.utils.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Determine if using SQLite (for testing) or PostgreSQL (for production)
is_sqlite = "sqlite" in settings.DATABASE_URL

# Create async engine with appropriate pool settings
if is_sqlite:
    # SQLite doesn't support connection pooling the same way
    engine_config = {
        "echo": settings.ENVIRONMENT == "development",
        "poolclass": StaticPool,
    }
else:
    # PostgreSQL with connection pooling
    engine_config = {
        "echo": settings.ENVIRONMENT == "development",
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
        "connect_args": {"timeout": 10}
    }

database_url = settings.DATABASE_URL
if not is_sqlite:
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(database_url, **engine_config)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
