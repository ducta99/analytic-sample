"""
Analytics Service - API routes and main application.
"""
import logging
from fastapi import FastAPI, Query, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
import asyncio
import json
from kafka import KafkaConsumer

from shared.utils.exceptions import CryptoAnalyticsException
from analytics_service.app.calculations import (
    MovingAverageCalculator,
    VolatilityCalculator,
    CorrelationCalculator,
    RSICalculator,
    MACDCalculator
)

logger = logging.getLogger(__name__)

# Mock price data storage (in production, would use database)
price_history = {}
kafka_consumer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    global kafka_consumer
    
    logger.info("Starting Analytics Service...")
    
    # Initialize Kafka consumer
    try:
        kafka_consumer = KafkaConsumer(
            'price_updates',
            bootstrap_servers=['kafka:29092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )
        logger.info("Connected to Kafka consumer")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {str(e)}")
    
    yield
    
    logger.info("Shutting down Analytics Service...")
    if kafka_consumer:
        kafka_consumer.close()


# Create FastAPI app
app = FastAPI(
    title="Analytics Service",
    description="Real-time analytics and metrics computation service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CryptoAnalyticsException)
async def crypto_exception_handler(request, exc: CryptoAnalyticsException):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": exc.code, "message": exc.message}
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "analytics-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }


@app.get("/api/analytics/moving-average/{coin_id}")
async def get_moving_average(
    coin_id: str,
    period: int = Query(20, ge=5, le=200),
    method: str = Query("sma", regex="^(sma|ema)$")
):
    """
    Get moving average for a coin.
    
    - **coin_id**: Cryptocurrency symbol (e.g., 'btc')
    - **period**: Number of periods for MA (default 20)
    - **method**: 'sma' for Simple MA or 'ema' for Exponential MA
    """
    # Get mock price data
    prices = price_history.get(coin_id.lower(), [])
    
    if not prices:
        raise HTTPException(status_code=404, detail=f"No price data for {coin_id}")
    
    if method == "sma":
        ma = MovingAverageCalculator.calculate_sma(prices, period)
    else:
        ma = MovingAverageCalculator.calculate_ema(prices, period)
    
    if ma is None:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data for period {period}"
        )
    
    return {
        "success": True,
        "data": {
            "coin_id": coin_id,
            "method": method,
            "period": period,
            "value": ma,
            "timestamp": datetime.utcnow()
        }
    }


@app.get("/api/analytics/volatility/{coin_id}")
async def get_volatility(
    coin_id: str,
    period: int = Query(20, ge=5, le=200)
):
    """
    Get volatility for a coin.
    
    - **coin_id**: Cryptocurrency symbol
    - **period**: Number of periods for volatility calculation
    """
    prices = price_history.get(coin_id.lower(), [])
    
    if not prices:
        raise HTTPException(status_code=404, detail=f"No price data for {coin_id}")
    
    volatility = VolatilityCalculator.calculate_volatility(prices, period)
    
    if volatility is None:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data for period {period}"
        )
    
    return {
        "success": True,
        "data": {
            "coin_id": coin_id,
            "volatility": volatility,
            "period": period,
            "timestamp": datetime.utcnow()
        }
    }


@app.get("/api/analytics/correlation")
async def get_correlation(
    coin1: str = Query(...),
    coin2: str = Query(...)
):
    """
    Get correlation between two coins.
    
    - **coin1**: First cryptocurrency symbol
    - **coin2**: Second cryptocurrency symbol
    """
    prices1 = price_history.get(coin1.lower(), [])
    prices2 = price_history.get(coin2.lower(), [])
    
    if not prices1 or not prices2:
        raise HTTPException(
            status_code=404,
            detail=f"Price data missing for {coin1 if not prices1 else coin2}"
        )
    
    correlation = CorrelationCalculator.calculate_correlation(prices1, prices2)
    
    if correlation is None:
        raise HTTPException(
            status_code=400,
            detail="Insufficient data for correlation calculation"
        )
    
    return {
        "success": True,
        "data": {
            "coin1": coin1,
            "coin2": coin2,
            "correlation": correlation,
            "timestamp": datetime.utcnow()
        }
    }


@app.get("/api/analytics/rsi/{coin_id}")
async def get_rsi(
    coin_id: str,
    period: int = Query(14, ge=5, le=50)
):
    """Get RSI (Relative Strength Index) for a coin."""
    prices = price_history.get(coin_id.lower(), [])
    
    if not prices:
        raise HTTPException(status_code=404, detail=f"No price data for {coin_id}")
    
    rsi = RSICalculator.calculate_rsi(prices, period)
    
    if rsi is None:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data for RSI calculation"
        )
    
    return {
        "success": True,
        "data": {
            "coin_id": coin_id,
            "rsi": rsi,
            "period": period,
            "signal": "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral",
            "timestamp": datetime.utcnow()
        }
    }


@app.get("/api/analytics/macd/{coin_id}")
async def get_macd(coin_id: str):
    """Get MACD (Moving Average Convergence Divergence) for a coin."""
    prices = price_history.get(coin_id.lower(), [])
    
    if not prices:
        raise HTTPException(status_code=404, detail=f"No price data for {coin_id}")
    
    macd = MACDCalculator.calculate_macd(prices)
    
    if macd is None:
        raise HTTPException(
            status_code=400,
            detail="Insufficient data for MACD calculation"
        )
    
    return {
        "success": True,
        "data": {
            "coin_id": coin_id,
            **macd,
            "timestamp": datetime.utcnow()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
