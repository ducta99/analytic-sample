"""
Shared response models and utilities.
"""
from typing import Optional, Any, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel


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
