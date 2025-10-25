"""
Shared response models and utilities.
"""
from typing import Optional, Any, Generic, TypeVar, Dict
from datetime import datetime
from pydantic import BaseModel
from fastapi import JSONResponse


T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapper."""
    success: bool = True
    data: Optional[T] = None
    meta: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    success: bool = False
    error: dict  # {"code": str, "message": str}


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = 0
    limit: int = 100
    
    def validate(self) -> None:
        if self.skip < 0:
            raise ValueError("skip must be non-negative")
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("limit must be between 1 and 1000")


def success_response(
    data: Any = None,
    meta: Optional[Dict] = None,
    status_code: int = 200
) -> JSONResponse:
    """Create standardized success response.
    
    Args:
        data: Response data payload
        meta: Optional metadata (timestamp, etc)
        status_code: HTTP status code
    
    Returns:
        JSONResponse with success format
    """
    if meta is None:
        meta = {"timestamp": datetime.utcnow().isoformat()}
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data,
            "meta": meta
        }
    )


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Dict] = None
) -> JSONResponse:
    """Create standardized error response.
    
    Args:
        code: Error code (e.g., RESOURCE_NOT_FOUND)
        message: Error message
        status_code: HTTP status code
        details: Optional error details
    
    Returns:
        JSONResponse with error format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
