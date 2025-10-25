"""
Test configuration and fixtures for sentiment service.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
from unittest.mock import Mock, AsyncMock

# Test database URL
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    
    async with engine.begin() as conn:
        # Create all tables
        from shared.utils.database import Base
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create test database session."""
    async_session_local = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_local() as session:
        yield session


@pytest_asyncio.fixture
def mock_redis():
    """Create mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.scan = AsyncMock(return_value=(0, []))
    return redis_mock


@pytest_asyncio.fixture
def mock_kafka_producer():
    """Create mock Kafka producer."""
    producer = Mock()
    producer.send = Mock(return_value=AsyncMock())
    producer.close = Mock()
    return producer


@pytest.fixture
def sample_articles():
    """Sample news articles for testing."""
    from datetime import datetime
    
    return [
        {
            "title": "Bitcoin Surges Above $50,000 on Positive Sentiment",
            "description": "Cryptocurrency investors show bullish signals",
            "url": "https://example.com/1",
            "source_name": "CryptoNews",
            "published_at": datetime.utcnow(),
            "content": "Bitcoin has surged above $50,000...",
            "image_url": "https://example.com/image1.jpg"
        },
        {
            "title": "Ethereum Network Upgrade Brings Negative Reactions",
            "description": "Some developers express concerns",
            "url": "https://example.com/2",
            "source_name": "TechCrypto",
            "published_at": datetime.utcnow(),
            "content": "The recent upgrade has caused...",
            "image_url": "https://example.com/image2.jpg"
        }
    ]
