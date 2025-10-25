"""
Market Data Service main application.
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.utils.exceptions import CryptoAnalyticsException
from market_data_service.app.routes import router, broadcast_price_update
from market_data_service.app.clients import (
    BinanceWebSocketClient,
    KafkaProducerClient
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global clients
binance_client = None
kafka_client = None
price_stream_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global binance_client, kafka_client, price_stream_task
    
    # Startup
    logger.info("Starting Market Data Service...")
    
    # Initialize Kafka producer
    kafka_client = KafkaProducerClient("kafka:29092")
    kafka_client.connect()
    
    # Initialize Binance client and start streaming
    coins = ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "USDT"]
    binance_client = BinanceWebSocketClient(coins)
    
    # Start price streaming in background
    async def stream_prices():
        async for price_update in binance_client.connect():
            try:
                # Publish to Kafka
                await kafka_client.publish("price_updates", price_update)
                
                # Broadcast to WebSocket clients
                await broadcast_price_update(price_update.model_dump(mode='json'))
            
            except Exception as e:
                logger.error(f"Error in price stream: {str(e)}")
    
    price_stream_task = asyncio.create_task(stream_prices())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Market Data Service...")
    if price_stream_task:
        price_stream_task.cancel()
    if binance_client:
        await binance_client.close()
    if kafka_client:
        kafka_client.close()


# Create FastAPI app
app = FastAPI(
    title="Market Data Service",
    description="Real-time cryptocurrency price streaming service",
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


# Exception handlers
@app.exception_handler(CryptoAnalyticsException)
async def crypto_exception_handler(request, exc: CryptoAnalyticsException):
    """Handle custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )


# Include routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
