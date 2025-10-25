"""
Sentiment Service - NLP sentiment analysis.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info("Starting Sentiment Service...")
    yield
    logger.info("Shutting down Sentiment Service...")


app = FastAPI(
    title="Sentiment Service",
    description="NLP sentiment analysis service for cryptocurrency news",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sentiment-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }


@app.get("/api/sentiment/{coin_id}")
async def get_sentiment(coin_id: str):
    """Get sentiment score for a coin."""
    return {
        "success": True,
        "data": {
            "coin_id": coin_id,
            "sentiment_score": 0.5,
            "positive_pct": 55,
            "negative_pct": 25,
            "neutral_pct": 20,
            "timestamp": datetime.utcnow()
        }
    }


@app.get("/api/sentiment/{coin_id}/trend")
async def get_sentiment_trend(coin_id: str):
    """Get sentiment trend for a coin."""
    return {
        "success": True,
        "data": {
            "coin_id": coin_id,
            "trend": "positive",
            "change": "+5%",
            "timestamp": datetime.utcnow()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
