"""
Scheduled sentiment analysis tasks.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from shared.utils.config import settings

logger = logging.getLogger(__name__)


class SentimentScheduler:
    """Scheduler for periodic sentiment analysis tasks."""
    
    # Default top coins to analyze
    DEFAULT_COINS = [
        "bitcoin", "ethereum", "binancecoin", "cardano", "solana",
        "ripple", "polkadot", "dogecoin", "avalanche-2", "chainlink",
        "litecoin", "polygon", "uniswap", "cosmos", "monero"
    ]
    
    def __init__(self, db_session_factory: async_sessionmaker):
        """Initialize scheduler.
        
        Args:
            db_session_factory: SQLAlchemy async session factory
        """
        self.db_factory = db_session_factory
        self.tasks = []
        self._running = False
    
    async def start(self):
        """Start scheduled tasks."""
        logger.info("Starting sentiment scheduler")
        self._running = True
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._sentiment_update_loop()),
            asyncio.create_task(self._news_fetch_loop()),
        ]
    
    async def stop(self):
        """Stop scheduled tasks."""
        logger.info("Stopping sentiment scheduler")
        self._running = False
        
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    async def _sentiment_update_loop(self):
        """Periodically update sentiment scores."""
        while self._running:
            try:
                await self._update_sentiment_batch(self.DEFAULT_COINS)
                # Update every 1 hour
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"Error in sentiment update loop: {e}")
                await asyncio.sleep(60)
    
    async def _news_fetch_loop(self):
        """Periodically fetch and analyze news."""
        while self._running:
            try:
                await self._fetch_and_analyze_news(self.DEFAULT_COINS)
                # Fetch every 30 minutes
                await asyncio.sleep(1800)
            except Exception as e:
                logger.error(f"Error in news fetch loop: {e}")
                await asyncio.sleep(60)
    
    async def _update_sentiment_batch(self, coin_ids: List[str]) -> int:
        """Update sentiment scores for multiple coins.
        
        Args:
            coin_ids: List of coin IDs to analyze
        
        Returns:
            Number of coins updated
        """
        try:
            async with self.db_factory() as session:
                from sentiment_service.app.nlp.classifier import EnsembleSentimentAnalyzer
                from sentiment_service.app.storage.sentiment_store import SentimentStore
                from sentiment_service.app.ingestors.newsapi import NewsAPIClient
                
                analyzer = EnsembleSentimentAnalyzer()
                store = SentimentStore(session)
                newsapi_key = settings.NEWSAPI_KEY if hasattr(settings, 'NEWSAPI_KEY') else None
                
                updated = 0
                
                # Use NewsAPI for articles if key available
                if newsapi_key:
                    try:
                        async with NewsAPIClient(newsapi_key) as client:
                            articles = await client.fetch_crypto_news(coin_ids, hours=24)
                            
                            if articles:
                                # Analyze articles in batch
                                texts = [a.title + " " + (a.description or "") for a in articles]
                                sentiments = analyzer.distilbert.classify_batch(texts)
                                
                                # Calculate average sentiment by coin
                                coin_sentiments = {}
                                for coin_id in coin_ids:
                                    coin_articles = [a for a in articles if coin_id.lower() in (a.description or a.title).lower()]
                                    if coin_articles:
                                        coin_sentiment_scores = sentiments[:len(coin_articles)]
                                        avg_score = sum(s.score for s in coin_sentiment_scores) / len(coin_sentiment_scores)
                                        avg_positive = sum(s.positive_pct for s in coin_sentiment_scores) / len(coin_sentiment_scores)
                                        avg_negative = sum(s.negative_pct for s in coin_sentiment_scores) / len(coin_sentiment_scores)
                                        avg_neutral = sum(s.neutral_pct for s in coin_sentiment_scores) / len(coin_sentiment_scores)
                                        
                                        label = "positive" if avg_positive > avg_negative else ("negative" if avg_negative > avg_positive else "neutral")
                                        
                                        # Save sentiment
                                        await store.save_sentiment(
                                            coin_id=coin_id,
                                            sentiment_score=avg_score,
                                            positive_pct=avg_positive,
                                            negative_pct=avg_negative,
                                            neutral_pct=avg_neutral,
                                            label=label,
                                            source="news",
                                            article_count=len(coin_articles)
                                        )
                                        updated += 1
                                        
                                        logger.info(f"Updated sentiment for {coin_id}: {label} ({avg_score:.2f})")
                            
                            await session.commit()
                    
                    except Exception as e:
                        logger.error(f"Error fetching news for sentiment: {e}")
                        await session.rollback()
                
                logger.info(f"Updated sentiment for {updated} coins")
                return updated
        
        except Exception as e:
            logger.error(f"Error in batch sentiment update: {e}")
            return 0
    
    async def _fetch_and_analyze_news(self, coin_ids: List[str]) -> int:
        """Fetch and analyze news articles.
        
        Args:
            coin_ids: List of coin IDs
        
        Returns:
            Number of articles analyzed
        """
        try:
            async with self.db_factory() as session:
                from sentiment_service.app.ingestors.newsapi import NewsAPIClient
                from sentiment_service.app.nlp.classifier import SentimentClassifier
                from sentiment_service.app.storage.sentiment_store import SentimentStore
                
                newsapi_key = settings.NEWSAPI_KEY if hasattr(settings, 'NEWSAPI_KEY') else None
                if not newsapi_key:
                    logger.warning("NewsAPI key not configured, skipping news fetch")
                    return 0
                
                classifier = SentimentClassifier()
                store = SentimentStore(session)
                analyzed = 0
                
                try:
                    async with NewsAPIClient(newsapi_key) as client:
                        articles = await client.fetch_crypto_news(coin_ids, hours=24)
                        
                        for article in articles:
                            # Check if article already stored
                            existing = await session.execute(
                                "SELECT id FROM news_articles WHERE url = %s",
                                (article.url,)
                            )
                            if existing.scalar():
                                continue
                            
                            # Classify sentiment
                            sentiment = classifier.classify(article.title + " " + (article.description or ""))
                            
                            # Find associated coins
                            for coin_id in coin_ids:
                                if coin_id.lower() in (article.title + article.description or "").lower():
                                    await store.save_article(
                                        coin_id=coin_id,
                                        title=article.title,
                                        description=article.description,
                                        url=article.url,
                                        source_name=article.source_name,
                                        published_at=article.published_at,
                                        content=article.content,
                                        image_url=article.image_url
                                    )
                                    analyzed += 1
                        
                        await session.commit()
                
                except Exception as e:
                    logger.error(f"Error analyzing news: {e}")
                    await session.rollback()
                
                logger.info(f"Analyzed {analyzed} articles")
                return analyzed
        
        except Exception as e:
            logger.error(f"Error in news fetch and analyze: {e}")
            return 0
    
    async def trigger_sentiment_update(self, coin_ids: Optional[List[str]] = None) -> int:
        """Manually trigger sentiment update.
        
        Args:
            coin_ids: Specific coins to update (uses defaults if None)
        
        Returns:
            Number of coins updated
        """
        coins = coin_ids or self.DEFAULT_COINS
        return await self._update_sentiment_batch(coins)
    
    async def trigger_news_fetch(self, coin_ids: Optional[List[str]] = None) -> int:
        """Manually trigger news fetch.
        
        Args:
            coin_ids: Specific coins to fetch for
        
        Returns:
            Number of articles analyzed
        """
        coins = coin_ids or self.DEFAULT_COINS
        return await self._fetch_and_analyze_news(coins)


# Global scheduler instance
_scheduler: Optional[SentimentScheduler] = None


def get_scheduler() -> Optional[SentimentScheduler]:
    """Get global scheduler instance.
    
    Returns:
        Scheduler instance or None if not initialized
    """
    return _scheduler


async def init_scheduler(db_session_factory: async_sessionmaker) -> SentimentScheduler:
    """Initialize and start scheduler.
    
    Args:
        db_session_factory: SQLAlchemy async session factory
    
    Returns:
        Scheduler instance
    """
    global _scheduler
    _scheduler = SentimentScheduler(db_session_factory)
    await _scheduler.start()
    return _scheduler


async def shutdown_scheduler():
    """Shutdown scheduler."""
    global _scheduler
    if _scheduler:
        await _scheduler.stop()
        _scheduler = None
