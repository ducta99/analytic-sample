"""
Portfolio Service - User portfolio management.
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
    logger.info("Starting Portfolio Service...")
    yield
    logger.info("Shutting down Portfolio Service...")


app = FastAPI(
    title="Portfolio Service",
    description="User portfolio management and performance tracking",
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
        "service": "portfolio-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }


@app.get("/api/portfolio")
async def list_portfolios(user_id: int):
    """List user portfolios."""
    return {
        "success": True,
        "data": {
            "portfolios": [],
            "count": 0
        }
    }


@app.get("/api/portfolio/{portfolio_id}")
async def get_portfolio(portfolio_id: int):
    """Get portfolio details."""
    return {
        "success": True,
        "data": {
            "id": portfolio_id,
            "name": "My Portfolio",
            "total_value": 10000,
            "total_gain_loss": 500,
            "roi_pct": 5.0
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
