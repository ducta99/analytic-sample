"""
Comprehensive tests for portfolio service endpoints and calculations.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Portfolio, PortfolioAsset, PortfolioHistory, Watchlist
from app.calculations.performance import PerformanceCalculator


class TestPortfolioCalculations:
    """Test portfolio performance calculations."""
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_performance_single_asset(
        self, db_session: AsyncSession, sample_asset: PortfolioAsset
    ):
        """Test portfolio performance with single asset."""
        portfolio = sample_asset.portfolio
        
        # Current prices
        current_prices = {"bitcoin": Decimal("60000.00")}
        
        # Calculate performance
        perf = PerformanceCalculator.calculate_portfolio_performance(
            [sample_asset], current_prices
        )
        
        assert perf["total_cost"] == Decimal("75000.00")  # 1.5 * 50000
        assert perf["total_value"] == Decimal("90000.00")  # 1.5 * 60000
        assert perf["total_gain_loss"] == Decimal("15000.00")
        assert perf["roi_pct"] == Decimal("20.00")
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_performance_multiple_assets(
        self, portfolio_with_assets: tuple[Portfolio, list[PortfolioAsset]]
    ):
        """Test portfolio performance with multiple assets."""
        portfolio, assets = portfolio_with_assets
        
        # Current prices
        current_prices = {
            "bitcoin": Decimal("70000.00"),
            "ethereum": Decimal("4000.00"),
            "cardano": Decimal("3.00"),
        }
        
        # Calculate performance
        perf = PerformanceCalculator.calculate_portfolio_performance(assets, current_prices)
        
        # Expected: (0.5 * 70000) + (5 * 4000) + (100 * 3) = 55000
        assert abs(perf["total_value"] - Decimal("55000.00")) < Decimal("1")
        
        # Expected cost: (0.5 * 60000) + (5 * 3500) + (100 * 2.5) = 47500
        assert abs(perf["total_cost"] - Decimal("47500.00")) < Decimal("1")
        
        # Gain/loss: 55000 - 47500 = 7500
        assert abs(perf["total_gain_loss"] - Decimal("7500.00")) < Decimal("1")
        
        # ROI: 7500 / 47500 * 100 ≈ 15.79%
        assert abs(perf["roi_pct"] - Decimal("15.79")) < Decimal("0.5")
    
    @pytest.mark.asyncio
    async def test_calculate_asset_performance(
        self, sample_asset: PortfolioAsset
    ):
        """Test individual asset performance calculation."""
        current_price = Decimal("65000.00")
        
        perf = PerformanceCalculator.calculate_asset_performance(
            sample_asset, current_price
        )
        
        assert perf["coin_id"] == "bitcoin"
        assert perf["quantity"] == Decimal("1.5")
        assert perf["cost_basis"] == Decimal("75000.00")
        assert perf["current_value"] == Decimal("97500.00")
        assert perf["gain_loss"] == Decimal("22500.00")
        assert perf["gain_loss_pct"] == Decimal("30.00")
    
    @pytest.mark.asyncio
    async def test_calculate_asset_allocation(
        self, portfolio_with_assets: tuple[Portfolio, list[PortfolioAsset]]
    ):
        """Test asset allocation calculation."""
        portfolio, assets = portfolio_with_assets
        
        current_prices = {
            "bitcoin": Decimal("70000.00"),
            "ethereum": Decimal("4000.00"),
            "cardano": Decimal("3.00"),
        }
        
        allocation = PerformanceCalculator.calculate_asset_allocation(
            assets, current_prices
        )
        
        assert len(allocation) == 3
        
        # Bitcoin: 35000 / 55000 = 63.64%
        btc_alloc = next(a for a in allocation if a["coin_id"] == "bitcoin")
        assert abs(btc_alloc["percentage"] - Decimal("63.64")) < Decimal("1")
        
        # Total should be ~100%
        total_pct = sum(a["percentage"] for a in allocation)
        assert abs(total_pct - Decimal("100.00")) < Decimal("1")
    
    @pytest.mark.asyncio
    async def test_identify_best_performers(
        self, portfolio_with_assets: tuple[Portfolio, list[PortfolioAsset]]
    ):
        """Test best/worst performer identification."""
        portfolio, assets = portfolio_with_assets
        
        current_prices = {
            "bitcoin": Decimal("70000.00"),  # +16.67% gain
            "ethereum": Decimal("2500.00"),  # -28.57% loss
            "cardano": Decimal("3.50"),      # +40% gain
        }
        
        best = PerformanceCalculator.identify_best_performers(
            assets, current_prices, top_n=1
        )
        worst = PerformanceCalculator.identify_best_performers(
            assets, current_prices, top_n=1, reverse=True
        )
        
        assert best[0]["coin_id"] == "cardano"  # +40%
        assert worst[0]["coin_id"] == "ethereum"  # -28.57%
    
    @pytest.mark.asyncio
    async def test_calculate_with_negative_return(
        self, sample_asset: PortfolioAsset
    ):
        """Test portfolio with negative returns."""
        current_price = Decimal("40000.00")  # Lower than purchase price
        
        perf = PerformanceCalculator.calculate_asset_performance(
            sample_asset, current_price
        )
        
        assert abs(perf["gain_loss"] - Decimal("-30000.00")) < Decimal("1")
        assert abs(perf["gain_loss_pct"] - Decimal("-40.00")) < Decimal("1")
    
    @pytest.mark.asyncio
    async def test_calculate_with_zero_quantity(
        self, db_session: AsyncSession, sample_portfolio: Portfolio
    ):
        """Test handling of zero quantity asset."""
        asset = PortfolioAsset(
            portfolio_id=sample_portfolio.id,
            coin_id="ethereum",
            quantity=Decimal("0.00"),
            purchase_price=Decimal("3500.00"),
            purchase_date=datetime.utcnow(),
        )
        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)
        
        current_prices = {"ethereum": Decimal("3500.00")}
        
        perf = PerformanceCalculator.calculate_portfolio_performance(
            [asset], current_prices
        )
        
        assert perf["total_cost"] == Decimal("0.00")
        assert perf["total_value"] == Decimal("0.00")


class TestPortfolioModels:
    """Test portfolio data models."""
    
    @pytest.mark.asyncio
    async def test_create_portfolio(
        self, db_session: AsyncSession
    ):
        """Test portfolio creation."""
        portfolio = Portfolio(
            user_id="test_user",
            name="Test Portfolio",
            description="Test description",
            is_active=True,
        )
        db_session.add(portfolio)
        await db_session.commit()
        await db_session.refresh(portfolio)
        
        assert portfolio.id is not None
        assert portfolio.user_id == "test_user"
        assert portfolio.is_active is True
        assert portfolio.created_at is not None
    
    @pytest.mark.asyncio
    async def test_portfolio_asset_unique_constraint(
        self, db_session: AsyncSession, sample_portfolio: Portfolio
    ):
        """Test that duplicate assets are rejected."""
        asset1 = PortfolioAsset(
            portfolio_id=sample_portfolio.id,
            coin_id="bitcoin",
            quantity=Decimal("1.0"),
            purchase_price=Decimal("50000.00"),
            purchase_date=datetime.utcnow(),
        )
        asset2 = PortfolioAsset(
            portfolio_id=sample_portfolio.id,
            coin_id="bitcoin",
            quantity=Decimal("2.0"),
            purchase_price=Decimal("60000.00"),
            purchase_date=datetime.utcnow(),
        )
        
        db_session.add(asset1)
        await db_session.commit()
        
        db_session.add(asset2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_watchlist_unique_constraint(
        self, db_session: AsyncSession
    ):
        """Test watchlist duplicate prevention."""
        wl1 = Watchlist(
            user_id="test_user",
            coin_id="bitcoin",
            added_at=datetime.utcnow(),
        )
        wl2 = Watchlist(
            user_id="test_user",
            coin_id="bitcoin",
            added_at=datetime.utcnow(),
        )
        
        db_session.add(wl1)
        await db_session.commit()
        
        db_session.add(wl2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_portfolio_history_snapshot(
        self, db_session: AsyncSession, sample_portfolio: Portfolio
    ):
        """Test portfolio history snapshot."""
        history = PortfolioHistory(
            portfolio_id=sample_portfolio.id,
            total_value=Decimal("100000.00"),
            total_cost=Decimal("95000.00"),
            total_gain_loss=Decimal("5000.00"),
            roi_pct=Decimal("5.26"),
            num_assets=2,
            snapshot_at=datetime.utcnow(),
        )
        db_session.add(history)
        await db_session.commit()
        await db_session.refresh(history)
        
        assert history.id is not None
        # Allow for some decimal precision variation in SQLite
        assert abs(history.roi_pct - Decimal("5.26")) < Decimal("0.1")


class TestPortfolioDatabaseQueries:
    """Test database queries for portfolio service."""
    
    @pytest.mark.asyncio
    async def test_get_portfolio_with_assets(
        self, db_session: AsyncSession, portfolio_with_assets: tuple[Portfolio, list[PortfolioAsset]]
    ):
        """Test retrieving portfolio with assets."""
        portfolio, assets = portfolio_with_assets
        
        stmt = select(Portfolio).filter_by(id=portfolio.id)
        result = await db_session.execute(stmt)
        fetched = result.scalar_one()
        
        assert fetched.id == portfolio.id
        assert len(fetched.assets) == 3
    
    @pytest.mark.asyncio
    async def test_get_user_portfolios(
        self, db_session: AsyncSession, multiple_portfolios: list[Portfolio]
    ):
        """Test retrieving all user portfolios."""
        stmt = select(Portfolio).filter_by(
            user_id="test_user_1", is_active=True
        )
        result = await db_session.execute(stmt)
        portfolios = result.scalars().all()
        
        assert len(portfolios) == 3
    
    @pytest.mark.asyncio
    async def test_soft_delete_portfolio(
        self, db_session: AsyncSession, sample_portfolio: Portfolio
    ):
        """Test soft delete functionality."""
        sample_portfolio.is_active = False
        await db_session.commit()
        
        stmt = select(Portfolio).filter_by(
            id=sample_portfolio.id, is_active=True
        )
        result = await db_session.execute(stmt)
        fetched = result.scalar()
        
        assert fetched is None
    
    @pytest.mark.asyncio
    async def test_get_portfolio_history(
        self, db_session: AsyncSession, sample_portfolio: Portfolio
    ):
        """Test retrieving portfolio history."""
        # Create multiple history snapshots
        now = datetime.utcnow()
        for i in range(5):
            history = PortfolioHistory(
                portfolio_id=sample_portfolio.id,
                total_value=Decimal("100000.00") + Decimal(i * 1000),
                total_cost=Decimal("95000.00"),
                total_gain_loss=Decimal("5000.00") + Decimal(i * 1000),
                roi_pct=Decimal("5.26"),
                num_assets=1,
                snapshot_at=now - timedelta(hours=i),
            )
            db_session.add(history)
        
        await db_session.commit()
        
        stmt = select(PortfolioHistory).filter_by(
            portfolio_id=sample_portfolio.id
        ).order_by(PortfolioHistory.snapshot_at.desc())
        result = await db_session.execute(stmt)
        history_records = result.scalars().all()
        
        assert len(history_records) == 5
        assert history_records[0].total_value == Decimal("104000.00")
    
    @pytest.mark.asyncio
    async def test_get_watchlist(
        self, db_session: AsyncSession
    ):
        """Test retrieving watchlist items."""
        user_id = "test_user"
        
        coins = ["bitcoin", "ethereum", "cardano"]
        for coin in coins:
            wl = Watchlist(
                user_id=user_id,
                coin_id=coin,
                added_at=datetime.utcnow(),
            )
            db_session.add(wl)
        
        await db_session.commit()
        
        stmt = select(Watchlist).filter_by(user_id=user_id)
        result = await db_session.execute(stmt)
        watchlist = result.scalars().all()
        
        assert len(watchlist) == 3


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_very_large_quantities(
        self, db_session: AsyncSession, sample_portfolio: Portfolio
    ):
        """Test handling of very large decimal quantities."""
        asset = PortfolioAsset(
            portfolio_id=sample_portfolio.id,
            coin_id="dogecoin",
            quantity=Decimal("999999999.99999999"),  # Max precision
            purchase_price=Decimal("0.50"),
            purchase_date=datetime.utcnow(),
        )
        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)
        
        assert asset.quantity == Decimal("999999999.99999999")
    
    @pytest.mark.asyncio
    async def test_very_small_prices(
        self, db_session: AsyncSession, sample_portfolio: Portfolio
    ):
        """Test handling of very small prices."""
        asset = PortfolioAsset(
            portfolio_id=sample_portfolio.id,
            coin_id="shib",
            quantity=Decimal("1000000.00"),
            purchase_price=Decimal("0.00000001"),
            purchase_date=datetime.utcnow(),
        )
        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)
        
        current_prices = {"shib": Decimal("0.00000002")}
        perf = PerformanceCalculator.calculate_asset_performance(
            asset, current_prices["shib"]
        )
        
        assert perf["cost_basis"] == Decimal("10.00")
        assert perf["current_value"] == Decimal("20.00")
    
    @pytest.mark.asyncio
    async def test_empty_portfolio_allocation(
        self, sample_portfolio: Portfolio
    ):
        """Test allocation calculation for empty portfolio."""
        allocation = PerformanceCalculator.calculate_asset_allocation([], {})
        
        assert allocation == []
    
    @pytest.mark.asyncio
    async def test_missing_current_prices(
        self, sample_asset: PortfolioAsset
    ):
        """Test handling of missing current prices."""
        # Empty price dict
        perf = PerformanceCalculator.calculate_portfolio_performance(
            [sample_asset], {}
        )
        
        # Should handle gracefully - treat as 0 current price
        assert perf["total_value"] == Decimal("0.00")
