"""
Portfolio management endpoints.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from decimal import Decimal
import logging

from shared.utils.database import get_db_session
from shared.utils.responses import success_response, error_response
from app.models import Portfolio, PortfolioAsset, PortfolioHistory
from app.calculations.performance import PerformanceCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("")
async def create_portfolio(
    user_id: int,
    name: str = Body(..., min_length=1, max_length=100),
    description: Optional[str] = Body(None, max_length=500),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new portfolio.
    
    Args:
        user_id: User ID (from auth token in real implementation)
        name: Portfolio name
        description: Optional portfolio description
        db: Database session
    
    Returns:
        Created portfolio
    """
    try:
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=description,
            is_active=True
        )
        
        db.add(portfolio)
        await db.flush()
        await db.refresh(portfolio)
        
        return success_response({
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "name": portfolio.name,
            "description": portfolio.description,
            "created_at": portfolio.created_at.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        await db.rollback()
        return error_response(
            code="PORTFOLIO_CREATE_ERROR",
            message="Failed to create portfolio",
            status_code=500
        )


@router.get("")
async def list_portfolios(
    user_id: int = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db_session)
):
    """List user's portfolios.
    
    Args:
        user_id: User ID
        db: Database session
    
    Returns:
        List of portfolios
    """
    try:
        stmt = select(Portfolio).where(
            Portfolio.user_id == user_id,
            Portfolio.is_active == True
        ).order_by(Portfolio.created_at.desc())
        
        result = await db.execute(stmt)
        portfolios = result.scalars().all()
        
        return success_response({
            "portfolios": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "created_at": p.created_at.isoformat(),
                    "num_assets": len(p.assets)
                }
                for p in portfolios
            ],
            "total": len(portfolios)
        })
    
    except Exception as e:
        logger.error(f"Error listing portfolios: {e}")
        return error_response(
            code="PORTFOLIO_LIST_ERROR",
            message="Failed to list portfolios",
            status_code=500
        )


@router.get("/{portfolio_id}")
async def get_portfolio(
    portfolio_id: int,
    user_id: int = Query(..., description="User ID for auth check"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get portfolio details.
    
    Args:
        portfolio_id: Portfolio ID
        user_id: User ID (for auth check)
        db: Database session
    
    Returns:
        Portfolio details
    """
    try:
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
        
        return success_response({
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "name": portfolio.name,
            "description": portfolio.description,
            "num_assets": len(portfolio.assets),
            "created_at": portfolio.created_at.isoformat(),
            "updated_at": portfolio.updated_at.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return error_response(
            code="PORTFOLIO_GET_ERROR",
            message="Failed to get portfolio",
            status_code=500
        )


@router.put("/{portfolio_id}")
async def update_portfolio(
    portfolio_id: int,
    user_id: int = Query(...),
    name: Optional[str] = Body(None, min_length=1, max_length=100),
    description: Optional[str] = Body(None, max_length=500),
    db: AsyncSession = Depends(get_db_session)
):
    """Update portfolio details.
    
    Args:
        portfolio_id: Portfolio ID
        user_id: User ID (for auth)
        name: New portfolio name
        description: New description
        db: Database session
    
    Returns:
        Updated portfolio
    """
    try:
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
        
        if name:
            portfolio.name = name
        if description is not None:
            portfolio.description = description
        
        portfolio.updated_at = datetime.utcnow()
        await db.flush()
        
        return success_response({
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "updated_at": portfolio.updated_at.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error updating portfolio: {e}")
        await db.rollback()
        return error_response(
            code="PORTFOLIO_UPDATE_ERROR",
            message="Failed to update portfolio",
            status_code=500
        )


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Soft delete a portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        user_id: User ID (for auth)
        db: Database session
    
    Returns:
        Success message
    """
    try:
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
        
        # Soft delete
        portfolio.is_active = False
        portfolio.updated_at = datetime.utcnow()
        await db.flush()
        
        return success_response({"message": "Portfolio deleted"})
    
    except Exception as e:
        logger.error(f"Error deleting portfolio: {e}")
        await db.rollback()
        return error_response(
            code="PORTFOLIO_DELETE_ERROR",
            message="Failed to delete portfolio",
            status_code=500
        )


@router.post("/{portfolio_id}/assets")
async def add_asset(
    portfolio_id: int,
    user_id: int = Query(...),
    coin_id: str = Body(..., min_length=1, max_length=50),
    quantity: float = Body(..., gt=0),
    purchase_price: float = Body(..., gt=0),
    purchase_date: Optional[datetime] = Body(None),
    db: AsyncSession = Depends(get_db_session)
):
    """Add asset to portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        user_id: User ID (for auth)
        coin_id: Cryptocurrency ID
        quantity: Quantity to add
        purchase_price: Purchase price per unit
        purchase_date: Purchase date (defaults to now)
        db: Database session
    
    Returns:
        Added asset
    """
    try:
        # Verify portfolio ownership
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
        
        # Check if asset already exists
        stmt = select(PortfolioAsset).where(
            PortfolioAsset.portfolio_id == portfolio_id,
            PortfolioAsset.coin_id == coin_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing asset
            existing.quantity += Decimal(str(quantity))
            existing.updated_at = datetime.utcnow()
        else:
            # Create new asset
            asset = PortfolioAsset(
                portfolio_id=portfolio_id,
                coin_id=coin_id,
                quantity=Decimal(str(quantity)),
                purchase_price=Decimal(str(purchase_price)),
                purchase_date=purchase_date or datetime.utcnow()
            )
            db.add(asset)
        
        await db.flush()
        
        return success_response({
            "coin_id": coin_id,
            "quantity": float(quantity),
            "purchase_price": purchase_price,
            "message": "Asset added successfully"
        })
    
    except Exception as e:
        logger.error(f"Error adding asset: {e}")
        await db.rollback()
        return error_response(
            code="ASSET_ADD_ERROR",
            message="Failed to add asset",
            status_code=500
        )


@router.put("/{portfolio_id}/assets/{coin_id}")
async def update_asset(
    portfolio_id: int,
    coin_id: str,
    user_id: int = Query(...),
    quantity: Optional[float] = Body(None, gt=0),
    purchase_price: Optional[float] = Body(None, gt=0),
    db: AsyncSession = Depends(get_db_session)
):
    """Update asset in portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        coin_id: Cryptocurrency ID
        user_id: User ID (for auth)
        quantity: New quantity
        purchase_price: New purchase price
        db: Database session
    
    Returns:
        Updated asset
    """
    try:
        # Verify ownership
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
        
        # Get asset
        stmt = select(PortfolioAsset).where(
            PortfolioAsset.portfolio_id == portfolio_id,
            PortfolioAsset.coin_id == coin_id
        )
        result = await db.execute(stmt)
        asset = result.scalar_one_or_none()
        
        if not asset:
            return error_response(
                code="ASSET_NOT_FOUND",
                message="Asset not found",
                status_code=404
            )
        
        if quantity is not None:
            asset.quantity = Decimal(str(quantity))
        if purchase_price is not None:
            asset.purchase_price = Decimal(str(purchase_price))
        
        asset.updated_at = datetime.utcnow()
        await db.flush()
        
        return success_response({
            "coin_id": coin_id,
            "quantity": float(asset.quantity),
            "purchase_price": float(asset.purchase_price),
            "updated_at": asset.updated_at.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error updating asset: {e}")
        await db.rollback()
        return error_response(
            code="ASSET_UPDATE_ERROR",
            message="Failed to update asset",
            status_code=500
        )


@router.delete("/{portfolio_id}/assets/{coin_id}")
async def remove_asset(
    portfolio_id: int,
    coin_id: str,
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Remove asset from portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        coin_id: Cryptocurrency ID
        user_id: User ID (for auth)
        db: Database session
    
    Returns:
        Success message
    """
    try:
        # Verify ownership
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
        
        # Delete asset
        stmt = delete(PortfolioAsset).where(
            PortfolioAsset.portfolio_id == portfolio_id,
            PortfolioAsset.coin_id == coin_id
        )
        await db.execute(stmt)
        await db.flush()
        
        return success_response({"message": "Asset removed"})
    
    except Exception as e:
        logger.error(f"Error removing asset: {e}")
        await db.rollback()
        return error_response(
            code="ASSET_DELETE_ERROR",
            message="Failed to remove asset",
            status_code=500
        )
