"""
Tests for sentiment storage layer.
"""
import pytest
from datetime import datetime
from sentiment_service.app.storage.sentiment_store import SentimentStore
from sentiment_service.app.models import SentimentScore as SentimentScoreModel, NewsArticle


class TestSentimentStore:
    """Tests for sentiment storage operations."""
    
    @pytest.fixture
    async def store(self, db_session, mock_redis):
        """Create sentiment store instance."""
        return SentimentStore(db_session, redis_client=mock_redis)
    
    @pytest.mark.asyncio
    async def test_save_sentiment(self, store, db_session):
        """Test saving sentiment to database."""
        result = await store.save_sentiment(
            coin_id="bitcoin",
            sentiment_score=0.75,
            positive_pct=75.0,
            negative_pct=15.0,
            neutral_pct=10.0,
            label="positive",
            source="news",
            article_count=25
        )
        
        assert result is not None
        assert result.coin_id == "bitcoin"
        assert result.score == 0.75
        assert result.label == "positive"
        assert result.article_count == 25
    
    @pytest.mark.asyncio
    async def test_get_latest_sentiment(self, store, db_session):
        """Test retrieving latest sentiment."""
        # Save sentiment
        await store.save_sentiment(
            coin_id="ethereum",
            sentiment_score=0.5,
            positive_pct=50.0,
            negative_pct=30.0,
            neutral_pct=20.0,
            label="positive"
        )
        
        # Retrieve
        sentiment = await store.get_latest_sentiment("ethereum")
        
        assert sentiment is not None
        assert sentiment.coin_id == "ethereum"
        assert sentiment.score == 0.5
    
    @pytest.mark.asyncio
    async def test_get_latest_sentiment_not_found(self, store):
        """Test getting non-existent sentiment returns None."""
        sentiment = await store.get_latest_sentiment("nonexistent_coin")
        assert sentiment is None
    
    @pytest.mark.asyncio
    async def test_get_sentiment_trend(self, store, db_session):
        """Test retrieving sentiment trend."""
        # Save multiple sentiments
        for i in range(3):
            await store.save_sentiment(
                coin_id="bitcoin",
                sentiment_score=0.5 + (i * 0.1),
                positive_pct=50.0,
                negative_pct=30.0,
                neutral_pct=20.0,
                label="positive"
            )
        
        # Get trend
        trend = await store.get_sentiment_trend("bitcoin", hours=24)
        
        assert len(trend) == 3
        assert all(s.coin_id == "bitcoin" for s in trend)
    
    @pytest.mark.asyncio
    async def test_save_article(self, store):
        """Test saving news article."""
        result = await store.save_article(
            coin_id="bitcoin",
            title="Bitcoin Hits New High",
            description="Bitcoin reaches record price",
            url="https://example.com/article1",
            source_name="CryptoNews",
            published_at=datetime.utcnow(),
            content="Full article content here"
        )
        
        assert result is not None
        assert result.coin_id == "bitcoin"
        assert result.title == "Bitcoin Hits New High"
        assert result.url == "https://example.com/article1"
    
    @pytest.mark.asyncio
    async def test_get_recent_articles(self, store):
        """Test retrieving recent articles."""
        # Save articles
        for i in range(5):
            await store.save_article(
                coin_id="ethereum",
                title=f"Ethereum Update {i}",
                description="Description",
                url=f"https://example.com/article{i}",
                source_name="TechNews",
                published_at=datetime.utcnow()
            )
        
        # Retrieve
        articles = await store.get_recent_articles("ethereum", limit=3)
        
        assert len(articles) == 3
        assert all(a.coin_id == "ethereum" for a in articles)
    
    @pytest.mark.asyncio
    async def test_cache_sentiment(self, store, mock_redis):
        """Test sentiment caching to Redis."""
        # Create sentiment
        sentiment = SentimentScoreModel(
            coin_id="bitcoin",
            score=0.75,
            positive_pct=75.0,
            negative_pct=15.0,
            neutral_pct=10.0,
            label="positive"
        )
        
        # Cache it
        result = await store._cache_sentiment(sentiment)
        
        assert result is True
        mock_redis.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_invalidate_sentiment_cache(self, store, mock_redis):
        """Test cache invalidation."""
        result = await store.invalidate_sentiment_cache("bitcoin")
        
        assert result is True
        mock_redis.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_sentiment_without_cache(self, db_session):
        """Test storage without Redis cache."""
        store = SentimentStore(db_session, redis_client=None)
        
        # Should work without cache
        result = await store.save_sentiment(
            coin_id="cardano",
            sentiment_score=0.6,
            positive_pct=60.0,
            negative_pct=20.0,
            neutral_pct=20.0,
            label="positive"
        )
        
        assert result is not None
        assert result.coin_id == "cardano"


class TestSentimentDataPersistence:
    """Tests for sentiment data persistence."""
    
    @pytest.mark.asyncio
    async def test_sentiment_persists_across_queries(self, db_session):
        """Test sentiment data persists in database."""
        store = SentimentStore(db_session)
        
        # Save
        await store.save_sentiment(
            coin_id="solana",
            sentiment_score=0.8,
            positive_pct=80.0,
            negative_pct=10.0,
            neutral_pct=10.0,
            label="positive"
        )
        
        # Retrieve
        result = await store.get_latest_sentiment("solana")
        
        assert result is not None
        assert result.score == 0.8
        assert result.label == "positive"
    
    @pytest.mark.asyncio
    async def test_article_unique_url_constraint(self, store):
        """Test articles have unique URLs."""
        url = "https://example.com/unique-article"
        
        # Save first article
        await store.save_article(
            coin_id="bitcoin",
            title="Article 1",
            description="Desc",
            url=url,
            source_name="News",
            published_at=datetime.utcnow()
        )
        
        # Attempt to save duplicate - should fail or skip
        with pytest.raises(Exception):
            await store.save_article(
                coin_id="ethereum",
                title="Article 2",
                description="Desc",
                url=url,
                source_name="News2",
                published_at=datetime.utcnow()
            )


class TestSentimentAggregation:
    """Tests for sentiment aggregation."""
    
    @pytest.mark.asyncio
    async def test_trend_calculation(self, store):
        """Test sentiment trend calculations."""
        scores = [0.2, 0.5, 0.8, 0.6, 0.4]
        
        # Save sentiments with varying scores
        for score in scores:
            await store.save_sentiment(
                coin_id="bitcoin",
                sentiment_score=score,
                positive_pct=60.0,
                negative_pct=20.0,
                neutral_pct=20.0,
                label="positive"
            )
        
        trend = await store.get_sentiment_trend("bitcoin", hours=24)
        
        assert len(trend) == len(scores)
        trend_scores = [s.score for s in trend]
        assert trend_scores == sorted(trend_scores)  # Ordered by timestamp
