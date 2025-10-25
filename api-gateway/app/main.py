"""
API Gateway - Central routing and request handling.
"""
import logging
import os
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import httpx
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime
import time
import uuid

from shared.utils.auth import verify_token
from shared.utils.exceptions import AuthenticationError, RateLimitError, ErrorCode
from shared.utils.logging_config import get_logger, set_request_id, request_context
from shared.utils.metrics import get_metrics
from app.middleware.error_handler import setup_exception_handlers, setup_error_middleware
from app.middleware.request_id import RequestIDMiddleware, get_request_id
from app.middleware.prometheus import PrometheusMiddleware
from app import schemas

logger = get_logger(__name__, "api-gateway")

# Service URLs
SERVICES = {
    "user": os.getenv("USER_SERVICE_URL", "http://localhost:8001"),
    "market": os.getenv("MARKET_SERVICE_URL", "http://localhost:8002"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8003"),
    "sentiment": os.getenv("SENTIMENT_SERVICE_URL", "http://localhost:8004"),
    "portfolio": os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8005"),
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
    title="Cryptocurrency Analytics Platform - API Gateway",
    description="Central API Gateway for real-time crypto analytics, portfolio tracking, and sentiment analysis. Provides unified access to all microservices with authentication, rate limiting, and request routing.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "Support",
        "email": "support@cryptoanalytics.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Setup exception handlers
setup_exception_handlers(app)
setup_error_middleware(app)

# Add Prometheus metrics middleware
app.add_middleware(
    PrometheusMiddleware,
    skip_paths=["/health", "/metrics"]
)

# Add request ID tracking middleware (must be early)
app.add_middleware(RequestIDMiddleware)

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
    set_request_id(request_id)
    start_time = time.time()
    
    logger.info(f"Starting: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(f"Completed: {request.method} {request.url.path} in {process_time:.3f}s with status {response.status_code}")
    
    return response


# Exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceptions."""
    raise RateLimitError(
        message="Rate limit exceeded. Please try again later.",
        retry_after=60
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


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from starlette.responses import Response
    return Response(content=get_metrics(), media_type="text/plain")


# User routes proxy
@app.post(
    "/api/users/register",
    tags=["Authentication"],
    responses={
        200: {"model": schemas.AuthResponse, "description": "User registered successfully"},
        400: {"model": schemas.ErrorResponse, "description": "Validation error"},
        409: {"model": schemas.ErrorResponse, "description": "User already exists"},
        429: {"description": "Rate limit exceeded"},
        502: {"model": schemas.ErrorResponse, "description": "User service unavailable"}
    },
    summary="Register new user",
    description="Create a new user account with email and password. Password must be at least 8 characters."
)
@limiter.limit("5/minute")
async def register(request: Request, body: schemas.UserRegisterRequest):
    """Register new user (proxied to user-service)."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id
    
    try:
        response = await call_downstream_service(
            f"{SERVICES['user']}/register",
            "POST",
            json=body.model_dump()
        )
        logger.info(f"[{request_id}] User registration proxied successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] User service error: {str(e)}")
        raise HTTPException(status_code=502, detail="User service unavailable")


@app.post(
    "/api/users/login",
    tags=["Authentication"],
    responses={
        200: {"model": schemas.AuthResponse, "description": "Login successful"},
        401: {"model": schemas.ErrorResponse, "description": "Invalid credentials"},
        429: {"description": "Rate limit exceeded"},
        502: {"model": schemas.ErrorResponse, "description": "User service unavailable"}
    },
    summary="Login user",
    description="Authenticate user with email and password. Returns JWT access and refresh tokens."
)
@limiter.limit("5/minute")
async def login(request: Request, body: schemas.UserLoginRequest):
    """Login user (proxied to user-service)."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id
    
    try:
        response = await call_downstream_service(
            f"{SERVICES['user']}/login",
            "POST",
            json=body.model_dump()
        )
        logger.info(f"[{request_id}] User login proxied successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] User service error: {str(e)}")
        raise HTTPException(status_code=502, detail="User service unavailable")


@app.post(
    "/api/users/refresh",
    tags=["Authentication"],
    responses={
        200: {"model": schemas.AuthResponse, "description": "Token refreshed successfully"},
        401: {"model": schemas.ErrorResponse, "description": "Invalid refresh token"},
        502: {"model": schemas.ErrorResponse, "description": "User service unavailable"}
    },
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token."
)
async def refresh_token(request: Request, body: schemas.TokenRefreshRequest):
    """Refresh access token (proxied to user-service)."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id
    
    try:
        response = await call_downstream_service(
            f"{SERVICES['user']}/refresh",
            "POST",
            json=body.model_dump()
        )
        logger.info(f"[{request_id}] Token refresh proxied successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] User service error: {str(e)}")
        raise HTTPException(status_code=502, detail="User service unavailable")


# Market Data routes proxy
@app.get(
    "/api/market/health",
    tags=["Market Data"],
    responses={
        200: {"model": schemas.HealthResponse, "description": "Service is healthy"},
        502: {"model": schemas.ErrorResponse, "description": "Service unavailable"}
    },
    summary="Market service health check",
    description="Check if the market data service is running and healthy."
)
async def market_health(request: Request):
    """Market service health (proxied)."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id
    
    try:
        response = await call_downstream_service(
            f"{SERVICES['market']}/health",
            "GET"
        )
        logger.info(f"[{request_id}] Market service health check successful")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Market service error: {str(e)}")
        raise HTTPException(status_code=502, detail="Market service unavailable")


# Analytics routes proxy
@app.get(
    "/api/analytics/moving-average/{coin_id}",
    tags=["Analytics"],
    responses={
        200: {"model": schemas.MovingAverageResponse, "description": "Moving average calculated successfully"},
        400: {"model": schemas.ErrorResponse, "description": "Invalid parameters"},
        404: {"model": schemas.ErrorResponse, "description": "Coin not found"},
        502: {"model": schemas.ErrorResponse, "description": "Analytics service unavailable"}
    },
    summary="Calculate moving average",
    description="Calculate Simple Moving Average (SMA) or Exponential Moving Average (EMA) for a cryptocurrency over a specified period."
)
async def get_moving_average(
    coin_id: str,
    period: int = 20,
    method: str = "sma",
    request: Request = None
):
    """Get moving average for coin (proxied to analytics-service)."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id if request else ""
    
    try:
        response = await call_downstream_service(
            f"{SERVICES['analytics']}/api/analytics/moving-average/{coin_id}",
            "GET",
            params={"period": period, "method": method}
        )
        logger.info(f"[{request_id}] Moving average calculation proxied successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Analytics service error: {str(e)}")
        raise HTTPException(status_code=502, detail="Analytics service unavailable")


@app.get(
    "/api/analytics/volatility/{coin_id}",
    tags=["Analytics"],
    responses={
        200: {"model": schemas.VolatilityResponse, "description": "Volatility calculated successfully"},
        400: {"model": schemas.ErrorResponse, "description": "Invalid parameters"},
        404: {"model": schemas.ErrorResponse, "description": "Coin not found"},
        502: {"model": schemas.ErrorResponse, "description": "Analytics service unavailable"}
    },
    summary="Calculate volatility",
    description="Calculate price volatility (standard deviation) for a cryptocurrency over a specified period."
)
async def get_volatility(coin_id: str, period: int = 20, request: Request = None):
    """Get volatility for coin (proxied to analytics-service)."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id if request else ""
    
    try:
        response = await call_downstream_service(
            f"{SERVICES['analytics']}/api/analytics/volatility/{coin_id}",
            "GET",
            params={"period": period}
        )
        logger.info(f"[{request_id}] Volatility calculation proxied successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Analytics service error: {str(e)}")
        raise HTTPException(status_code=502, detail="Analytics service unavailable")


@app.get(
    "/api/analytics/correlation",
    tags=["Analytics"],
    responses={
        200: {"model": schemas.CorrelationResponse, "description": "Correlation calculated successfully"},
        400: {"model": schemas.ErrorResponse, "description": "Invalid parameters"},
        404: {"model": schemas.ErrorResponse, "description": "Coin not found"},
        502: {"model": schemas.ErrorResponse, "description": "Analytics service unavailable"}
    },
    summary="Calculate correlation",
    description="Calculate price correlation coefficient between two cryptocurrencies."
)
async def get_correlation(coin1: str, coin2: str, request: Request = None):
    """Get correlation between coins (proxied to analytics-service)."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id if request else ""
    
    try:
        response = await call_downstream_service(
            f"{SERVICES['analytics']}/api/analytics/correlation",
            "GET",
            params={"coin1": coin1, "coin2": coin2}
        )
        logger.info(f"[{request_id}] Correlation analysis proxied successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Analytics service error: {str(e)}")
        raise HTTPException(status_code=502, detail="Analytics service unavailable")


# ============================================================================
# Portfolio Service Routes
# ============================================================================

@app.get("/api/portfolio", tags=["Portfolio"])
async def get_portfolios(request: Request):
    """Get all portfolios for the authenticated user."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id if request else ""
    
    try:
        params = dict(request.query_params)  # Forward query parameters
        target_url = f"{SERVICES['portfolio']}/api/portfolio"
        logger.info(f"[{request_id}] Getting portfolios from portfolio-service")
        
        response = await call_downstream_service(target_url, "GET", params=params)
        logger.info(f"[{request_id}] Portfolios retrieved successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Portfolio service error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Portfolio service unavailable: {str(e)}")


@app.post("/api/portfolio", tags=["Portfolio"])
async def create_portfolio(request: Request):
    """Create a new portfolio."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id if request else ""
    
    try:
        body = await request.json()
        params = dict(request.query_params)  # Forward query parameters
        target_url = f"{SERVICES['portfolio']}/api/portfolio"
        logger.info(f"[{request_id}] Creating portfolio via portfolio-service")
        
        response = await call_downstream_service(target_url, "POST", json_data=body, params=params)
        logger.info(f"[{request_id}] Portfolio created successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Portfolio service error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Portfolio service unavailable: {str(e)}")


@app.get("/api/watchlist", tags=["Watchlist"])
async def get_watchlist(request: Request):
    """Get user's watchlist."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id if request else ""
    
    try:
        target_url = f"{SERVICES['portfolio']}/api/watchlist"
        logger.info(f"[{request_id}] Getting watchlist from portfolio-service")
        
        response = await call_downstream_service(target_url, "GET")
        logger.info(f"[{request_id}] Watchlist retrieved successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Portfolio service error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Watchlist service unavailable: {str(e)}")


@app.api_route("/api/portfolio/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def portfolio_proxy(path: str, request: Request):
    """Proxy all portfolio-related requests to portfolio service."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id if request else ""
    method = request.method
    
    try:
        # Get request body if present
        body = None
        if method in ["POST", "PUT"]:
            try:
                body = await request.json()
            except:
                pass
        
        # Get query parameters
        params = dict(request.query_params)
        
        # Build target URL
        target_url = f"{SERVICES['portfolio']}/api/portfolio/{path}"
        
        logger.info(f"[{request_id}] Proxying {method} to portfolio-service: {target_url}")
        
        # Make the downstream call
        response = await call_downstream_service(
            target_url,
            method,
            json_data=body,
            params=params
        )
        
        logger.info(f"[{request_id}] Portfolio request proxied successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Portfolio service error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Portfolio service unavailable: {str(e)}")


@app.api_route("/api/watchlist/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def watchlist_proxy(path: str, request: Request):
    """Proxy all watchlist-related requests to portfolio service."""
    from app.utils.service_client import call_downstream_service
    
    request_id = request.state.request_id if request else ""
    method = request.method
    
    try:
        # Get request body if present
        body = None
        if method in ["POST", "PUT"]:
            try:
                body = await request.json()
            except:
                pass
        
        # Get query parameters
        params = dict(request.query_params)
        
        # Build target URL
        target_url = f"{SERVICES['portfolio']}/api/watchlist/{path}"
        
        logger.info(f"[{request_id}] Proxying {method} to portfolio-service (watchlist): {target_url}")
        
        # Make the downstream call
        response = await call_downstream_service(
            target_url,
            method,
            json_data=body,
            params=params
        )
        
        logger.info(f"[{request_id}] Watchlist request proxied successfully")
        return response.json()
    except Exception as e:
        logger.error(f"[{request_id}] Portfolio service (watchlist) error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Watchlist service unavailable: {str(e)}")


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
