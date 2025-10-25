"""
Watchlist endpoints.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import logging

from shared.utils.database import get_db_session
from shared.utils.responses import success_response, error_response
from app.models import Watchlist

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.post("")
async def add_to_watchlist(
    user_id: int = Query(...),
    coin_id: str = Body(..., min_length=1, max_length=50),
    db: AsyncSession = Depends(get_db_session)
):
    """Add coin to watchlist.
    
    Args:
        user_id: User ID
        coin_id: Cryptocurrency ID
        db: Database session
    
    Returns:
        Added watchlist item
    """
    try:
        # Check if already in watchlist
        stmt = select(Watchlist).where(
            Watchlist.user_id == user_id,
            Watchlist.coin_id == coin_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return error_response(
                code="ALREADY_WATCHLISTED",
                message=f"{coin_id} is already in your watchlist",
                status_code=409
            )
        
        # Add to watchlist
        item = Watchlist(user_id=user_id, coin_id=coin_id)
        db.add(item)
        await db.flush()
        
        return success_response({
            "coin_id": coin_id,
            "added_at": item.added_at.isoformat(),
            "message": f"Added {coin_id} to watchlist"
        })
    
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        await db.rollback()
        return error_response(
            code="WATCHLIST_ADD_ERROR",
            message="Failed to add to watchlist",
            status_code=500
        )


@router.get("")
async def get_watchlist(
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's watchlist.
    
    Args:
        user_id: User ID
        db: Database session
    
    Returns:
        List of watchlisted coins
    """
    try:
        stmt = select(Watchlist).where(
            Watchlist.user_id == user_id
        ).order_by(Watchlist.added_at.desc())
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        return success_response({
            "coins": [
                {
                    "coin_id": item.coin_id,
                    "added_at": item.added_at.isoformat()
                }
                for item in items
            ],
            "total": len(items)
        })
    
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        return error_response(
            code="WATCHLIST_GET_ERROR",
            message="Failed to get watchlist",
            status_code=500
        )


@router.delete("/{coin_id}")
async def remove_from_watchlist(
    coin_id: str,
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Remove coin from watchlist.
    
    Args:
        coin_id: Cryptocurrency ID
        user_id: User ID
        db: Database session
    
    Returns:
        Success message
    """
    try:
        stmt = delete(Watchlist).where(
            Watchlist.user_id == user_id,
            Watchlist.coin_id == coin_id
        )
        result = await db.execute(stmt)
        await db.flush()
        
        if result.rowcount == 0:
            return error_response(
                code="NOT_IN_WATCHLIST",
                message=f"{coin_id} is not in your watchlist",
                status_code=404
            )
        
        return success_response({
            "coin_id": coin_id,
            "message": f"Removed {coin_id} from watchlist"
        })
    
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        await db.rollback()
        return error_response(
            code="WATCHLIST_REMOVE_ERROR",
            message="Failed to remove from watchlist",
            status_code=500
        )
