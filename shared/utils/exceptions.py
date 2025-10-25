"""
Shared exception classes for all services with standardized error codes.

Error Codes:
- 400: VALIDATION_ERROR - Invalid request parameters or body
- 401: AUTHENTICATION_ERROR - Invalid credentials or missing authentication
- 403: AUTHORIZATION_ERROR - Insufficient permissions for resource
- 404: RESOURCE_NOT_FOUND - Resource does not exist
- 409: CONFLICT - Resource already exists or state conflict
- 429: RATE_LIMITED - Rate limit exceeded
- 500: INTERNAL_ERROR - Server error
- 502: EXTERNAL_SERVICE_ERROR - External service failure
"""
from typing import Optional, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    
    # 400 Bad Request
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    
    # 401 Unauthorized
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    # 403 Forbidden
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # 404 Not Found
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    PORTFOLIO_NOT_FOUND = "PORTFOLIO_NOT_FOUND"
    COIN_NOT_FOUND = "COIN_NOT_FOUND"
    
    # 409 Conflict
    CONFLICT = "CONFLICT"
    DUPLICATE_USER = "DUPLICATE_USER"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    
    # 429 Too Many Requests
    RATE_LIMITED = "RATE_LIMITED"
    
    # 500 Internal Server Error
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    
    # 502 Bad Gateway
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    KAFKA_ERROR = "KAFKA_ERROR"
    EXCHANGE_CONNECTION_ERROR = "EXCHANGE_CONNECTION_ERROR"


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
    """Raised when validation fails (400 Bad Request)."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR.value,
            status_code=400,
            details=details
        )


class InvalidParameterError(CryptoAnalyticsException):
    """Raised when request parameter is invalid (400 Bad Request)."""
    
    def __init__(self, param_name: str, reason: str):
        super().__init__(
            message=f"Invalid parameter '{param_name}': {reason}",
            code=ErrorCode.INVALID_PARAMETER.value,
            status_code=400
        )


class AuthenticationError(CryptoAnalyticsException):
    """Raised when authentication fails (401 Unauthorized)."""
    
    def __init__(self, message: str = "Authentication failed", code: str = ErrorCode.AUTHENTICATION_ERROR.value):
        super().__init__(
            message=message,
            code=code,
            status_code=401
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid (401 Unauthorized)."""
    
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, ErrorCode.INVALID_CREDENTIALS.value)


class TokenExpiredError(AuthenticationError):
    """Raised when token has expired (401 Unauthorized)."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, ErrorCode.TOKEN_EXPIRED.value)


class TokenInvalidError(AuthenticationError):
    """Raised when token is invalid (401 Unauthorized)."""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, ErrorCode.TOKEN_INVALID.value)


class AuthorizationError(CryptoAnalyticsException):
    """Raised when user lacks required permissions (403 Forbidden)."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            code=ErrorCode.AUTHORIZATION_ERROR.value,
            status_code=403
        )


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions (403 Forbidden)."""
    
    def __init__(self, resource: str = "resource"):
        super().__init__(f"Insufficient permissions to access {resource}")


class ResourceNotFoundError(CryptoAnalyticsException):
    """Raised when a requested resource is not found (404 Not Found)."""
    
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            code=ErrorCode.RESOURCE_NOT_FOUND.value,
            status_code=404
        )


class UserNotFoundError(ResourceNotFoundError):
    """Raised when user is not found (404 Not Found)."""
    
    def __init__(self, user_id: Any):
        self.message = f"User with ID '{user_id}' not found"
        self.code = ErrorCode.USER_NOT_FOUND.value
        self.status_code = 404
        self.details = None
        # Don't call super().__init__ to avoid double message format


class PortfolioNotFoundError(ResourceNotFoundError):
    """Raised when portfolio is not found (404 Not Found)."""
    
    def __init__(self, portfolio_id: Any):
        self.message = f"Portfolio with ID '{portfolio_id}' not found"
        self.code = ErrorCode.PORTFOLIO_NOT_FOUND.value
        self.status_code = 404
        self.details = None


class CoinNotFoundError(ResourceNotFoundError):
    """Raised when coin is not found (404 Not Found)."""
    
    def __init__(self, coin_id: Any):
        self.message = f"Coin '{coin_id}' not found"
        self.code = ErrorCode.COIN_NOT_FOUND.value
        self.status_code = 404
        self.details = None


class ConflictError(CryptoAnalyticsException):
    """Raised when there's a conflict (e.g., duplicate entry) (409 Conflict)."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT.value,
            status_code=409,
            details=details
        )


class DuplicateUserError(ConflictError):
    """Raised when user already exists (409 Conflict)."""
    
    def __init__(self, field: str = "user"):
        super().__init__(f"A {field} with this identifier already exists")


class DuplicateEntryError(ConflictError):
    """Raised when entry already exists (409 Conflict)."""
    
    def __init__(self, resource: str = "resource"):
        super().__init__(f"{resource} already exists")


class RateLimitError(CryptoAnalyticsException):
    """Raised when rate limit is exceeded (429 Too Many Requests)."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMITED.value,
            status_code=429,
            details={"retry_after": retry_after} if retry_after else None
        )


class DatabaseError(CryptoAnalyticsException):
    """Raised when database operations fail (500 Internal Server Error)."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.DATABASE_ERROR.value,
            status_code=500,
            details=details
        )


class CacheError(CryptoAnalyticsException):
    """Raised when cache operations fail (500 Internal Server Error)."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code=ErrorCode.CACHE_ERROR.value,
            status_code=500,
            details=details
        )


class ExternalServiceError(CryptoAnalyticsException):
    """Raised when external service calls fail (502 Bad Gateway)."""
    
    def __init__(self, service: str, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"{service} error: {message}",
            code=ErrorCode.EXTERNAL_SERVICE_ERROR.value,
            status_code=502,
            details=details
        )


class KafkaError(ExternalServiceError):
    """Raised when Kafka operations fail (502 Bad Gateway)."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__("Kafka", message, details)
        self.code = ErrorCode.KAFKA_ERROR.value


class ExchangeConnectionError(ExternalServiceError):
    """Raised when exchange connection fails (502 Bad Gateway)."""
    
    def __init__(self, exchange: str, message: str, details: Optional[Any] = None):
        super().__init__(exchange, message, details)
        self.code = ErrorCode.EXCHANGE_CONNECTION_ERROR.value
