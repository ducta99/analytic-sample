"""
NewsAPI integration for fetching cryptocurrency news articles.

Uses NewsAPI (https://newsapi.org) to fetch latest crypto news.
Requires NEWSAPI_KEY environment variable.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NewsArticle(BaseModel):
    """Model for a news article."""
    
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    url: str = Field(..., pattern=r"https?://")
    source_name: str = Field(..., alias="source_name", max_length=100)
    published_at: datetime
    content: Optional[str] = Field(None, max_length=5000)
    image_url: Optional[str] = Field(None, alias="urlToImage")
    
    class Config:
        populate_by_name = True


class NewsAPIClient:
    """Client for NewsAPI service."""
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: str):
        """Initialize NewsAPI client.
        
        Args:
            api_key: NewsAPI key from https://newsapi.org
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_crypto_news(
        self,
        coin_names: List[str],
        hours: int = 24,
        language: str = "en",
        sort_by: str = "publishedAt"
    ) -> List[NewsArticle]:
        """Fetch latest cryptocurrency news.
        
        Args:
            coin_names: List of cryptocurrency names to search for (e.g., ['bitcoin', 'ethereum'])
            hours: Look back period in hours (default: 24)
            language: Article language code (default: 'en')
            sort_by: Sort order - 'publishedAt', 'relevancy', 'popularity' (default: 'publishedAt')
        
        Returns:
            List of NewsArticle objects
            
        Raises:
            ValueError: If API key is invalid
            aiohttp.ClientError: If network request fails
        """
        if not self.session:
            raise RuntimeError("NewsAPI client not initialized. Use async with context manager.")
        
        articles = []
        from_date = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d")
        
        try:
            for coin in coin_names:
                # Search for coin-related news
                query = f'"{coin}" cryptocurrency'
                params = {
                    "q": query,
                    "from": from_date,
                    "language": language,
                    "sortBy": sort_by,
                    "apiKey": self.api_key,
                    "pageSize": 100
                }
                
                async with self.session.get(
                    f"{self.BASE_URL}/everything",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 401:
                        raise ValueError(f"Invalid NewsAPI key: {response.status}")
                    if response.status == 429:
                        logger.warning("NewsAPI rate limited, backing off")
                        continue
                    if response.status != 200:
                        logger.error(f"NewsAPI error: {response.status}")
                        continue
                    
                    data = await response.json()
                    
                    if data.get("status") == "error":
                        logger.error(f"NewsAPI error: {data.get('message')}")
                        continue
                    
                    for article_data in data.get("articles", []):
                        try:
                            # Parse article date
                            pub_date_str = article_data.get("publishedAt", "")
                            published_at = datetime.fromisoformat(
                                pub_date_str.replace("Z", "+00:00")
                            )
                            
                            article = NewsArticle(
                                title=article_data.get("title", ""),
                                description=article_data.get("description"),
                                url=article_data.get("url", ""),
                                source_name=article_data.get("source", {}).get("name", "Unknown"),
                                published_at=published_at,
                                content=article_data.get("content"),
                                image_url=article_data.get("urlToImage")
                            )
                            articles.append(article)
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Failed to parse article: {e}")
                            continue
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching news: {e}")
            raise
        
        return articles
    
    async def fetch_trending_topics(
        self,
        search_terms: List[str],
        hours: int = 24
    ) -> dict:
        """Analyze trending topics in crypto news.
        
        Args:
            search_terms: Terms to search for in recent articles
            hours: Look back period in hours
        
        Returns:
            Dictionary with topic trends and frequencies
        """
        from_date = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d")
        trends = {}
        
        try:
            for term in search_terms:
                params = {
                    "q": term,
                    "from": from_date,
                    "sortBy": "publishedAt",
                    "apiKey": self.api_key,
                    "pageSize": 100
                }
                
                async with self.session.get(
                    f"{self.BASE_URL}/everything",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        total_results = data.get("totalResults", 0)
                        trends[term] = {
                            "mentions": total_results,
                            "articles": len(data.get("articles", []))
                        }
        
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching trending topics: {e}")
        
        return trends


class CryptoCompareClient:
    """Client for CryptoCompare API (alternative news source)."""
    
    BASE_URL = "https://api.cryptocompare.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize CryptoCompare client.
        
        Args:
            api_key: Optional API key (free tier doesn't require it)
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_latest_news(
        self,
        coin_ids: List[str],
        limit: int = 100
    ) -> List[dict]:
        """Fetch latest news from CryptoCompare.
        
        Args:
            coin_ids: List of coin identifiers (e.g., ['bitcoin', 'ethereum'])
            limit: Maximum number of articles to fetch
        
        Returns:
            List of news articles
        """
        if not self.session:
            raise RuntimeError("CryptoCompare client not initialized. Use async with context manager.")
        
        articles = []
        
        try:
            # CryptoCompare returns recent news
            params = {
                "categories": "all",
                "limit": limit
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with self.session.get(
                f"{self.BASE_URL}/v2/news/",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    logger.error(f"CryptoCompare error: {response.status}")
                    return articles
                
                data = await response.json()
                
                for article in data.get("Data", []):
                    # Filter for coins of interest
                    article_coins = article.get("categories", "").lower().split("|")
                    if any(coin.lower() in article_coins for coin in coin_ids):
                        articles.append({
                            "title": article.get("title", ""),
                            "url": article.get("url", ""),
                            "source": article.get("source", "Unknown"),
                            "published_at": datetime.fromtimestamp(article.get("published_on", 0)),
                            "image_url": article.get("imageurl", ""),
                            "body": article.get("body", "")
                        })
        
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching CryptoCompare news: {e}")
        
        return articles
