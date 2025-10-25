"""
Test fixtures and configuration for portfolio service.
"""
import os
import sys
from decimal import Decimal
from datetime import datetime, timedelta
from typing import AsyncGenerator

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Configure for testing BEFORE importing other modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import StaticPool

from app.models import Portfolio, PortfolioAsset, PortfolioHistory, Watchlist, Base


# Test database setup
@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def sample_portfolio(db_session: AsyncSession) -> Portfolio:
    """Create sample portfolio."""
    portfolio = Portfolio(
        user_id="test_user_1",
        name="Test Portfolio",
        description="Test description",
        is_active=True,
    )
    db_session.add(portfolio)
    await db_session.commit()
    await db_session.refresh(portfolio)
    return portfolio


@pytest_asyncio.fixture
async def sample_asset(db_session: AsyncSession, sample_portfolio: Portfolio) -> PortfolioAsset:
    """Create sample portfolio asset."""
    asset = PortfolioAsset(
        portfolio_id=sample_portfolio.id,
        coin_id="bitcoin",
        quantity=Decimal("1.5"),
        purchase_price=Decimal("50000.00"),
        purchase_date=datetime.utcnow(),
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    return asset


@pytest_asyncio.fixture
async def sample_watchlist(db_session: AsyncSession) -> Watchlist:
    """Create sample watchlist entry."""
    watchlist = Watchlist(
        user_id="test_user_1",
        coin_id="ethereum",
        added_at=datetime.utcnow(),
    )
    db_session.add(watchlist)
    await db_session.commit()
    await db_session.refresh(watchlist)
    return watchlist


@pytest_asyncio.fixture
async def sample_history(db_session: AsyncSession, sample_portfolio: Portfolio) -> PortfolioHistory:
    """Create sample portfolio history."""
    history = PortfolioHistory(
        portfolio_id=sample_portfolio.id,
        total_value=Decimal("75000.00"),
        total_cost=Decimal("70000.00"),
        total_gain_loss=Decimal("5000.00"),
        roi_pct=Decimal("7.14"),
        num_assets=1,
        snapshot_at=datetime.utcnow(),
    )
    db_session.add(history)
    await db_session.commit()
    await db_session.refresh(history)
    return history


@pytest_asyncio.fixture
async def multiple_portfolios(db_session: AsyncSession) -> list[Portfolio]:
    """Create multiple test portfolios."""
    portfolios = []
    for i in range(3):
        portfolio = Portfolio(
            user_id="test_user_1",
            name=f"Portfolio {i+1}",
            description=f"Test portfolio {i+1}",
            is_active=True,
        )
        db_session.add(portfolio)
        portfolios.append(portfolio)
    
    await db_session.commit()
    for portfolio in portfolios:
        await db_session.refresh(portfolio)
    
    return portfolios


@pytest_asyncio.fixture
async def portfolio_with_assets(
    db_session: AsyncSession,
) -> tuple[Portfolio, list[PortfolioAsset]]:
    """Create portfolio with multiple assets."""
    portfolio = Portfolio(
        user_id="test_user_1",
        name="Multi-Asset Portfolio",
        description="Portfolio with multiple coins",
        is_active=True,
    )
    db_session.add(portfolio)
    await db_session.flush()
    
    assets = []
    coins = [
        ("bitcoin", Decimal("0.5"), Decimal("60000.00")),
        ("ethereum", Decimal("5.0"), Decimal("3500.00")),
        ("cardano", Decimal("100.0"), Decimal("2.50")),
    ]
    
    for coin_id, quantity, price in coins:
        asset = PortfolioAsset(
            portfolio_id=portfolio.id,
            coin_id=coin_id,
            quantity=quantity,
            purchase_price=price,
            purchase_date=datetime.utcnow() - timedelta(days=30),
        )
        db_session.add(asset)
        assets.append(asset)
    
    await db_session.commit()
    await db_session.refresh(portfolio)
    for asset in assets:
        await db_session.refresh(asset)
    
    return portfolio, assets
