"""
Centralized error handling middleware for API Gateway.

Provides consistent error responses across all endpoints with proper HTTP status codes,
error codes, and messages.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from shared.utils.exceptions import CryptoAnalyticsException, ErrorCode
from shared.utils.logging_config import get_request_id

logger = logging.getLogger(__name__)


def format_error_response(
    message: str,
    code: str = ErrorCode.INTERNAL_ERROR.value,
    status_code: int = 500,
    details: Optional[Any] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format a standardized error response.
    
    Args:
        message: Error message
        code: Error code from ErrorCode enum
        status_code: HTTP status code
        details: Additional error details
        request_id: Request ID for tracking
    
    Returns:
        Formatted error response dictionary
    """
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if request_id:
        response["request_id"] = request_id
    
    return response


async def handle_crypto_analytics_exception(
    request: Request,
    exc: CryptoAnalyticsException
) -> JSONResponse:
    """
    Handle CryptoAnalyticsException instances.
    
    Args:
        request: FastAPI request object
        exc: The exception to handle
    
    Returns:
        JSONResponse with proper status code and formatted error
    """
    request_id = get_request_id()
    
    logger.error(
        f"[{request_id}] {exc.code}: {exc.message}",
        extra={"details": exc.details}
    )
    
    error_response = format_error_response(
        message=exc.message,
        code=exc.code,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def handle_validation_error(
    request: Request,
    exc: PydanticValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors (422 Unprocessable Entity).
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation error
    
    Returns:
        JSONResponse with validation details
    """
    request_id = get_request_id()
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error.get("loc", ["unknown"])[1:])
        errors.append({
            "field": field or "general",
            "message": error.get("msg"),
            "type": error.get("type")
        })
    
    logger.warning(
        f"[{request_id}] Validation error for {request.method} {request.url.path}",
        extra={"errors": errors}
    )
    
    error_response = format_error_response(
        message="Validation failed",
        code=ErrorCode.VALIDATION_ERROR.value,
        status_code=422,
        details={"validation_errors": errors},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response
    )


async def handle_generic_exception(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle generic unhandled exceptions.
    
    Args:
        request: FastAPI request object
        exc: The exception to handle
    
    Returns:
        JSONResponse with generic error message
    """
    request_id = get_request_id()
    
    logger.exception(
        f"[{request_id}] Unhandled exception: {type(exc).__name__}: {str(exc)}"
    )
    
    # Don't expose internal error details in production
    error_response = format_error_response(
        message="Internal server error",
        code=ErrorCode.INTERNAL_ERROR.value,
        status_code=500,
        details=None,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )


async def handle_not_found(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle 404 Not Found errors.
    
    Args:
        request: FastAPI request object
        exc: The exception
    
    Returns:
        JSONResponse with 404 error
    """
    request_id = get_request_id()
    
    logger.warning(f"[{request_id}] Not found: {request.method} {request.url.path}")
    
    error_response = format_error_response(
        message=f"Endpoint {request.method} {request.url.path} not found",
        code=ErrorCode.RESOURCE_NOT_FOUND.value,
        status_code=404,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=404,
        content=error_response
    )


async def handle_method_not_allowed(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle 405 Method Not Allowed errors.
    
    Args:
        request: FastAPI request object
        exc: The exception
    
    Returns:
        JSONResponse with 405 error
    """
    request_id = get_request_id()
    
    logger.warning(f"[{request_id}] Method not allowed: {request.method} {request.url.path}")
    
    error_response = format_error_response(
        message=f"Method {request.method} not allowed on {request.url.path}",
        code="METHOD_NOT_ALLOWED",
        status_code=405,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=405,
        content=error_response
    )


def setup_exception_handlers(app):
    """
    Setup all exception handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(CryptoAnalyticsException)
    async def crypto_analytics_exception_handler(request: Request, exc: CryptoAnalyticsException):
        return await handle_crypto_analytics_exception(request, exc)
    
    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_error_handler(request: Request, exc: PydanticValidationError):
        return await handle_validation_error(request, exc)
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        return await handle_not_found(request, exc)
    
    @app.exception_handler(405)
    async def method_not_allowed_handler(request: Request, exc: Exception):
        return await handle_method_not_allowed(request, exc)
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return await handle_generic_exception(request, exc)


def setup_error_middleware(app):
    """
    Setup error handling middleware for consistent error responses.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.middleware("http")
    async def error_handling_middleware(request: Request, call_next):
        """Middleware to catch and format errors consistently."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the exception
            request_id = get_request_id()
            logger.exception(f"[{request_id}] Middleware caught exception: {type(exc).__name__}")
            
            # Handle the exception
            if isinstance(exc, CryptoAnalyticsException):
                return await handle_crypto_analytics_exception(request, exc)
            else:
                return await handle_generic_exception(request, exc)
