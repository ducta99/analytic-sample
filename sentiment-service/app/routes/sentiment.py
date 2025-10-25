"""
Sentiment endpoints.
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from shared.utils.database import get_db_session
from shared.utils.responses import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


@router.get("/{coin_id}")
async def get_sentiment(
    coin_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get latest sentiment score for a coin.
    
    Args:
        coin_id: Cryptocurrency ID (e.g., 'bitcoin', 'ethereum')
        db: Database session
    
    Returns:
        Latest sentiment score or 404 if not found
    """
    try:
        from app.storage.sentiment_store import SentimentStore
        
        store = SentimentStore(db)
        sentiment = await store.get_latest_sentiment(coin_id)
        
        if not sentiment:
            return error_response(
                code="SENTIMENT_NOT_FOUND",
                message=f"No sentiment data found for {coin_id}",
                status_code=404
            )
        
        return success_response({
            "coin_id": sentiment.coin_id,
            "sentiment_score": sentiment.score,
            "positive_pct": sentiment.positive_pct,
            "negative_pct": sentiment.negative_pct,
            "neutral_pct": sentiment.neutral_pct,
            "label": sentiment.label,
            "source": sentiment.source,
            "article_count": sentiment.article_count,
            "timestamp": sentiment.timestamp.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting sentiment for {coin_id}: {e}")
        return error_response(
            code="INTERNAL_ERROR",
            message="Failed to get sentiment data",
            status_code=500
        )


@router.get("/{coin_id}/trend")
async def get_sentiment_trend(
    coin_id: str,
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db_session)
):
    """Get sentiment trend for a coin over a period.
    
    Args:
        coin_id: Cryptocurrency ID
        hours: Look-back period in hours (1-720, default: 24)
        db: Database session
    
    Returns:
        List of sentiment scores ordered by timestamp
    """
    try:
        from app.storage.sentiment_store import SentimentStore
        
        store = SentimentStore(db)
        sentiments = await store.get_sentiment_trend(coin_id, hours=hours)
        
        if not sentiments:
            return success_response({
                "coin_id": coin_id,
                "trend": [],
                "period_hours": hours,
                "message": "No sentiment data available for this period"
            })
        
        # Calculate trend statistics
        scores = [s.score for s in sentiments]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        trend_direction = "positive" if avg_score > 0 else ("negative" if avg_score < 0 else "neutral")
        
        return success_response({
            "coin_id": coin_id,
            "period_hours": hours,
            "trend_direction": trend_direction,
            "average_score": round(avg_score, 4),
            "min_score": round(min_score, 4),
            "max_score": round(max_score, 4),
            "data_points": len(sentiments),
            "timeline": [
                {
                    "timestamp": s.timestamp.isoformat(),
                    "score": s.score,
                    "label": s.label,
                    "positive_pct": round(s.positive_pct, 2),
                    "negative_pct": round(s.negative_pct, 2),
                    "neutral_pct": round(s.neutral_pct, 2)
                }
                for s in sentiments
            ]
        })
    
    except Exception as e:
        logger.error(f"Error getting sentiment trend for {coin_id}: {e}")
        return error_response(
            code="INTERNAL_ERROR",
            message="Failed to get sentiment trend",
            status_code=500
        )


@router.get("/{coin_id}/news")
async def get_coin_news(
    coin_id: str,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session)
):
    """Get recent news articles for a coin.
    
    Args:
        coin_id: Cryptocurrency ID
        limit: Maximum number of articles (1-100)
        db: Database session
    
    Returns:
        List of recent news articles
    """
    try:
        from app.storage.sentiment_store import SentimentStore
        
        store = SentimentStore(db)
        articles = await store.get_recent_articles(coin_id, limit=limit)
        
        return success_response({
            "coin_id": coin_id,
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "description": a.description,
                    "url": a.url,
                    "source": a.source_name,
                    "published_at": a.published_at.isoformat(),
                    "sentiment_score": a.sentiment_score,
                    "sentiment_label": a.sentiment_label,
                    "image_url": a.image_url
                }
                for a in articles
            ],
            "total": len(articles)
        })
    
    except Exception as e:
        logger.error(f"Error getting news for {coin_id}: {e}")
        return error_response(
            code="INTERNAL_ERROR",
            message="Failed to get news articles",
            status_code=500
        )


@router.get("/compare/multi")
async def compare_sentiment(
    coins: str = Query(..., description="Comma-separated coin IDs"),
    db: AsyncSession = Depends(get_db_session)
):
    """Compare sentiment across multiple coins.
    
    Args:
        coins: Comma-separated coin IDs (e.g., 'bitcoin,ethereum,cardano')
        db: Database session
    
    Returns:
        Sentiment comparison for all coins
    """
    try:
        from app.storage.sentiment_store import SentimentStore
        
        coin_list = [c.strip() for c in coins.split(",") if c.strip()]
        
        if not coin_list:
            return error_response(
                code="INVALID_COINS",
                message="No valid coins provided",
                status_code=400
            )
        
        if len(coin_list) > 50:
            return error_response(
                code="TOO_MANY_COINS",
                message="Maximum 50 coins allowed for comparison",
                status_code=400
            )
        
        store = SentimentStore(db)
        results = []
        
        for coin_id in coin_list:
            sentiment = await store.get_latest_sentiment(coin_id)
            if sentiment:
                results.append({
                    "coin_id": sentiment.coin_id,
                    "sentiment_score": sentiment.score,
                    "positive_pct": sentiment.positive_pct,
                    "negative_pct": sentiment.negative_pct,
                    "neutral_pct": sentiment.neutral_pct,
                    "label": sentiment.label,
                    "timestamp": sentiment.timestamp.isoformat()
                })
        
        # Sort by sentiment score (most positive first)
        results.sort(key=lambda x: x["sentiment_score"], reverse=True)
        
        return success_response({
            "comparison": results,
            "total_coins": len(results),
            "requested_coins": len(coin_list),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error comparing sentiment: {e}")
        return error_response(
            code="INTERNAL_ERROR",
            message="Failed to compare sentiment",
            status_code=500
        )
