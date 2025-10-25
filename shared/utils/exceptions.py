"""
Shared exception classes for all services.
"""
from typing import Optional, Any


class CryptoAnalyticsException(Exception):
    """Base exception for all crypto analytics exceptions."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ValidationError(CryptoAnalyticsException):
    """Raised when validation fails."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class AuthenticationError(CryptoAnalyticsException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(CryptoAnalyticsException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403
        )


class ResourceNotFoundError(CryptoAnalyticsException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            code="RESOURCE_NOT_FOUND",
            status_code=404
        )


class ConflictError(CryptoAnalyticsException):
    """Raised when there's a conflict (e.g., duplicate entry)."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details
        )


class RateLimitError(CryptoAnalyticsException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="RATE_LIMITED",
            status_code=429
        )


class DatabaseError(CryptoAnalyticsException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details
        )


class ExternalServiceError(CryptoAnalyticsException):
    """Raised when external service calls fail."""
    
    def __init__(self, service: str, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"{service} error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=details
        )
