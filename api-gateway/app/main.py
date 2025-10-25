"""
API Gateway - Central routing and request handling.
"""
import logging
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime
import time
import uuid

from shared.utils.auth import verify_token
from shared.utils.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# Service URLs
SERVICES = {
    "user": "http://user-service:8001",
    "market": "http://market-data-service:8002",
    "analytics": "http://analytics-service:8003",
    "sentiment": "http://sentiment-service:8004",
}

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info("Starting API Gateway...")
    yield
    logger.info("Shutting down API Gateway...")


# Create FastAPI app
app = FastAPI(
    title="API Gateway",
    description="Central API Gateway for cryptocurrency analytics platform",
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


# Middleware for request logging and tracing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request ID and process time tracking."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(f"[{request_id}] Completed in {process_time:.3f}s")
    
    return response


# Exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceptions."""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later."
            }
        }
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }


# User routes proxy
@app.post("/api/users/register", tags=["users"])
@limiter.limit("5/minute")
async def register(request: Request):
    """Register new user (proxied to user-service)."""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['user']}/register",
                json=body
            )
            return response.json()
        except Exception as e:
            logger.error(f"User service error: {str(e)}")
            raise HTTPException(status_code=502, detail="User service unavailable")


@app.post("/api/users/login", tags=["users"])
@limiter.limit("5/minute")
async def login(request: Request):
    """Login user (proxied to user-service)."""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['user']}/login",
                json=body
            )
            return response.json()
        except Exception as e:
            logger.error(f"User service error: {str(e)}")
            raise HTTPException(status_code=502, detail="User service unavailable")


@app.post("/api/users/refresh", tags=["users"])
async def refresh_token(request: Request):
    """Refresh access token (proxied to user-service)."""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICES['user']}/refresh",
                json=body
            )
            return response.json()
        except Exception as e:
            logger.error(f"User service error: {str(e)}")
            raise HTTPException(status_code=502, detail="User service unavailable")


# Market Data routes proxy
@app.get("/api/market/health", tags=["market"])
async def market_health():
    """Market service health (proxied)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES['market']}/health")
            return response.json()
        except Exception as e:
            logger.error(f"Market service error: {str(e)}")
            raise HTTPException(status_code=502, detail="Market service unavailable")


# Analytics routes proxy
@app.get("/api/analytics/moving-average/{coin_id}", tags=["analytics"])
async def get_moving_average(coin_id: str, period: int = 20, method: str = "sma"):
    """Get moving average for coin (proxied to analytics-service)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SERVICES['analytics']}/api/analytics/moving-average/{coin_id}",
                params={"period": period, "method": method}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Analytics service error: {str(e)}")
            raise HTTPException(status_code=502, detail="Analytics service unavailable")


@app.get("/api/analytics/volatility/{coin_id}", tags=["analytics"])
async def get_volatility(coin_id: str, period: int = 20):
    """Get volatility for coin (proxied to analytics-service)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SERVICES['analytics']}/api/analytics/volatility/{coin_id}",
                params={"period": period}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Analytics service error: {str(e)}")
            raise HTTPException(status_code=502, detail="Analytics service unavailable")


@app.get("/api/analytics/correlation", tags=["analytics"])
async def get_correlation(coin1: str, coin2: str):
    """Get correlation between coins (proxied to analytics-service)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SERVICES['analytics']}/api/analytics/correlation",
                params={"coin1": coin1, "coin2": coin2}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Analytics service error: {str(e)}")
            raise HTTPException(status_code=502, detail="Analytics service unavailable")


# Catch-all for unmatched routes
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path: str, request: Request):
    """Catch-all route for 404."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Endpoint {request.method} /{path} not found"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
