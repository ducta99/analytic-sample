"""
Portfolio performance endpoints.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
import logging

from shared.utils.database import get_db_session
from shared.utils.responses import success_response, error_response
from portfolio_service.app.models import Portfolio, PortfolioAsset, PortfolioHistory
from portfolio_service.app.calculations.performance import PerformanceCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/{portfolio_id}/performance")
async def get_portfolio_performance(
    portfolio_id: int,
    user_id: int = Query(...),
    current_prices: Optional[str] = Query(None, description="JSON dict of coin_id: price"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get portfolio performance metrics.
    
    Args:
        portfolio_id: Portfolio ID
        user_id: User ID (for auth)
        current_prices: JSON string with current prices (use API in real implementation)
        db: Database session
    
    Returns:
        Portfolio performance metrics
    """
    try:
        # Get portfolio
        stmt = select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        )
        result = await db.execute(stmt)
        portfolio = result.scalar_one_or_none()
        
        if not portfolio:
            return error_response(
                code="PORTFOLIO_NOT_FOUND",
                message="Portfolio not found",
                status_code=404
            )
        
        # Get assets
        assets = portfolio.assets
        
        if not assets:
            return success_response({
                "portfolio_id": portfolio_id,
                "total_value": 0.0,
                "total_cost": 0.0,
                "total_gain_loss": 0.0,
                "roi_pct": 0.0,
                "num_assets": 0
            })
        
        # Parse prices (in real implementation, fetch from price service)
        import json
        if current_prices:
            try:
                prices = json.loads(current_prices)
                current_prices_map = {
                    k: Decimal(str(v)) for k, v in prices.items()
                }
            except (json.JSONDecodeError, ValueError):
                return error_response(
                    code="INVALID_PRICES",
                    message="Invalid price format",
                    status_code=400
                )
        else:
            # Default to purchase prices if not provided
            current_prices_map = {
                a.coin_id: a.purchase_price for a in assets
            }
        
        # Convert assets to dict format
        asset_dicts = [
            {
                'coin_id': a.coin_id,
                'quantity': a.quantity,
                'purchase_price': a.purchase_price,
                'purchase_date': a.purchase_date
            }
            for a in assets
        ]
        
        # Calculate performance
        perf = PerformanceCalculator.calculate_portfolio_performance(
            asset_dicts,
            current_prices_map
        )
        
        # Calculate asset allocation
        allocation = PerformanceCalculator.calculate_asset_allocation(
            asset_dicts,
            current_prices_map
        )
        
        # Get best/worst performers
        performers = PerformanceCalculator.identify_best_performers(
            asset_dicts,
            current_prices_map,
            limit=3
        )
        
        # Save history snapshot
        history = PortfolioHistory(
            portfolio_id=portfolio_id,
            total_value=perf.total_value,
            total_cost=perf.total_cost,
            total_gain_loss=perf.total_gain_loss,
            roi_pct=perf.roi_pct,
            num_assets=len(assets)
        )
        db.add(history)
        await db.flush()
        
        return success_response({
            "portfolio_id": portfolio_id,
            "total_value": float(perf.total_value),
            "total_cost": float(perf.total_cost),
            "total_gain_loss": float(perf.total_gain_loss),
            "roi_pct": perf.roi_pct,
            "num_assets": perf.num_assets,
            "asset_allocation": allocation,
            "best_performers": performers['best_performers'],
            "worst_performers": performers['worst_performers'],
            "calculated_at": perf.calculated_at.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error calculating performance: {e}")
        return error_response(
            code="PERFORMANCE_ERROR",
            message="Failed to calculate performance",
            status_code=500
        )


@router.get("/{portfolio_id}/asset-performance")
async def get_asset_performance(
    portfolio_id: int,
    user_id: int = Query(...),
    coin_id: Optional[str] = Query(None),
    current_prices: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """Get individual asset performance.
    
    Args:
        portfolio_id: Portfolio ID
        user_id: User ID (for auth)
        coin_id: Specific coin to get (optional, return all if omitted)
        current_prices: JSON with current prices
        db: Database session
    
    Returns:
        Asset performance metrics
    """
    try:
        # Get portfolio
        stmt = select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        )
        result = await db.execute(stmt)
        portfolio = result.scalar_one_or_none()
        
        if not portfolio:
            return error_response(
                code="PORTFOLIO_NOT_FOUND",
                message="Portfolio not found",
                status_code=404
            )
        
        # Parse prices
        import json
        if current_prices:
            try:
                prices = json.loads(current_prices)
                current_prices_map = {
                    k: Decimal(str(v)) for k, v in prices.items()
                }
            except (json.JSONDecodeError, ValueError):
                return error_response(
                    code="INVALID_PRICES",
                    message="Invalid price format",
                    status_code=400
                )
        else:
            current_prices_map = {
                a.coin_id: a.purchase_price for a in portfolio.assets
            }
        
        # Calculate performance for each asset
        asset_performances = []
        for asset in portfolio.assets:
            if coin_id and asset.coin_id != coin_id:
                continue
            
            perf = PerformanceCalculator.calculate_asset_performance(
                coin_id=asset.coin_id,
                quantity=asset.quantity,
                purchase_price=asset.purchase_price,
                current_price=current_prices_map.get(
                    asset.coin_id,
                    asset.purchase_price
                ),
                purchase_date=asset.purchase_date
            )
            asset_performances.append(perf)
        
        if not asset_performances:
            return error_response(
                code="ASSET_NOT_FOUND",
                message="No assets found",
                status_code=404
            )
        
        return success_response({
            "portfolio_id": portfolio_id,
            "assets": asset_performances,
            "total": len(asset_performances)
        })
    
    except Exception as e:
        logger.error(f"Error calculating asset performance: {e}")
        return error_response(
            code="ASSET_PERFORMANCE_ERROR",
            message="Failed to calculate asset performance",
            status_code=500
        )


@router.get("/{portfolio_id}/history")
async def get_portfolio_history(
    portfolio_id: int,
    user_id: int = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db_session)
):
    """Get portfolio performance history.
    
    Args:
        portfolio_id: Portfolio ID
        user_id: User ID (for auth)
        days: Number of days to look back
        db: Database session
    
    Returns:
        Historical performance data
    """
    try:
        # Get portfolio
        stmt = select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        )
        result = await db.execute(stmt)
        portfolio = result.scalar_one_or_none()
        
        if not portfolio:
            return error_response(
                code="PORTFOLIO_NOT_FOUND",
                message="Portfolio not found",
                status_code=404
            )
        
        # Get history
        from datetime import timedelta
        since = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(PortfolioHistory).where(
            PortfolioHistory.portfolio_id == portfolio_id,
            PortfolioHistory.snapshot_at >= since
        ).order_by(PortfolioHistory.snapshot_at)
        
        result = await db.execute(stmt)
        history = result.scalars().all()
        
        return success_response({
            "portfolio_id": portfolio_id,
            "period_days": days,
            "snapshots": [
                {
                    "total_value": float(h.total_value),
                    "total_cost": float(h.total_cost),
                    "total_gain_loss": float(h.total_gain_loss),
                    "roi_pct": h.roi_pct,
                    "num_assets": h.num_assets,
                    "snapshot_at": h.snapshot_at.isoformat()
                }
                for h in history
            ],
            "total_snapshots": len(history)
        })
    
    except Exception as e:
        logger.error(f"Error getting portfolio history: {e}")
        return error_response(
            code="HISTORY_ERROR",
            message="Failed to get portfolio history",
            status_code=500
        )
