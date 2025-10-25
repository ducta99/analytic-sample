"""
Portfolio Service - User portfolio management.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager

# Import routers
from app.routes import portfolio, performance, watchlist

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

# Include routers
app.include_router(portfolio.router)
app.include_router(performance.router)
app.include_router(watchlist.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "portfolio-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
