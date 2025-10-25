"""
Security hardening middleware for FastAPI applications.

Implements:
- CORS protection with strict origin validation
- CSRF token verification
- Security headers (CSP, X-Frame-Options, etc.)
- Input validation and sanitization
- Rate limiting per IP/user
- SQL injection prevention (via SQLAlchemy ORM)
- XSS protection
"""

import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Optional, Set
from urllib.parse import urlparse

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from shared.utils.logging_config import get_logger

logger = get_logger(__name__)

# Security headers to add to all responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",  # Prevent MIME type sniffing
    "X-Frame-Options": "DENY",  # Prevent clickjacking
    "X-XSS-Protection": "1; mode=block",  # Browser XSS protection
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",  # Force HTTPS
    "Referrer-Policy": "strict-origin-when-cross-origin",  # Control referrer info
    "Permissions-Policy": (
        "geolocation=(), microphone=(), camera=(), "
        "accelerometer=(), gyroscope=(), magnetometer=()"
    ),
}

# Content Security Policy
CSP_HEADER = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
    "img-src 'self' data: https:; "
    "font-src 'self' fonts.gstatic.com; "
    "connect-src 'self' http://localhost:* https:; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


class RateLimiter:
    """Token bucket rate limiter per IP/user."""

    def __init__(self, rate: int = 100, window: int = 60):
        """Initialize rate limiter.
        
        Args:
            rate: Max requests per window
            window: Time window in seconds
        """
        self.rate = rate
        self.window = window
        self.requests: dict = {}  # {ip: [(timestamp, count)]}

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier.
        
        Args:
            identifier: IP address or user ID
            
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window)

        if identifier not in self.requests:
            self.requests[identifier] = []

        # Remove old requests outside window
        self.requests[identifier] = [
            (ts, count)
            for ts, count in self.requests[identifier]
            if ts > window_start
        ]

        # Count requests in window
        total_requests = sum(count for _, count in self.requests[identifier])

        if total_requests >= self.rate:
            return False

        # Add current request
        self.requests[identifier].append((now, 1))
        return True

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier.
        
        Args:
            identifier: IP address or user ID
            
        Returns:
            Number of remaining requests
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window)

        if identifier not in self.requests:
            return self.rate

        # Count requests in window
        valid_requests = [
            (ts, count)
            for ts, count in self.requests[identifier]
            if ts > window_start
        ]
        total = sum(count for _, count in valid_requests)
        return max(0, self.rate - total)


class CSRFProtection:
    """CSRF token generation and validation."""

    def __init__(self, secret: str):
        """Initialize CSRF protection.
        
        Args:
            secret: Secret key for token generation
        """
        self.secret = secret.encode()
        self.valid_tokens: Set[str] = set()

    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            CSRF token
        """
        token = hmac.new(
            self.secret,
            session_id.encode(),
            hashlib.sha256,
        ).hexdigest()
        self.valid_tokens.add(token)
        return token

    def validate_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token.
        
        Args:
            token: Token from request
            session_id: Session identifier
            
        Returns:
            True if valid, False otherwise
        """
        expected = hmac.new(
            self.secret,
            session_id.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(token, expected)


class InputValidator:
    """Validate and sanitize user inputs."""

    DANGEROUS_PATTERNS = [
        "'",  # SQL injection
        '"',
        ";",
        "--",
        "/*",
        "*/",
        "xp_",  # SQL Server
        "sp_",
        "<script",  # XSS
        "javascript:",
        "onerror=",
        "onclick=",
    ]

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input.
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return ""

        # Truncate
        value = value[:max_length]

        # Remove null bytes
        value = value.replace("\x00", "")

        # Remove control characters
        value = "".join(
            c for c in value if ord(c) >= 32 or c in "\n\r\t"
        )

        return value

    @staticmethod
    def is_safe(value: str) -> bool:
        """Check if value contains dangerous patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if safe, False if suspicious
        """
        value_lower = value.lower()
        for pattern in InputValidator.DANGEROUS_PATTERNS:
            if pattern.lower() in value_lower:
                return False
        return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response.
        
        Args:
            request: HTTP request
            call_next: Next middleware
            
        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)

        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add CSP header
        response.headers["Content-Security-Policy"] = CSP_HEADER

        return response


class CORSProtectionMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS protection with strict validation."""

    def __init__(self, app, allowed_origins: list, allowed_methods: list = None):
        """Initialize CORS middleware.
        
        Args:
            app: FastAPI application
            allowed_origins: List of allowed origin URLs
            allowed_methods: List of allowed HTTP methods
        """
        super().__init__(app)
        self.allowed_origins = set(allowed_origins)
        self.allowed_methods = allowed_methods or [
            "GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"
        ]

    def _get_origin(self, request: Request) -> Optional[str]:
        """Extract and normalize origin from request.
        
        Args:
            request: HTTP request
            
        Returns:
            Normalized origin or None
        """
        origin = request.headers.get("origin")
        if not origin:
            return None

        try:
            parsed = urlparse(origin)
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            return None

    async def dispatch(self, request: Request, call_next) -> Response:
        """Validate and apply CORS headers.
        
        Args:
            request: HTTP request
            call_next: Next middleware
            
        Returns:
            HTTP response with CORS headers
        """
        origin = self._get_origin(request)

        # Handle preflight
        if request.method == "OPTIONS":
            if origin and origin in self.allowed_origins:
                return Response(
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": ", ".join(
                            self.allowed_methods
                        ),
                        "Access-Control-Allow-Headers": (
                            "Content-Type, Authorization, X-CSRF-Token"
                        ),
                        "Access-Control-Max-Age": "86400",
                    }
                )
            return Response(status_code=403)

        # Add CORS headers to response
        response = await call_next(request)

        if origin and origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting per IP address."""

    def __init__(
        self,
        app,
        rate: int = 100,
        window: int = 60,
        exempt_paths: list = None,
    ):
        """Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            rate: Max requests per window
            window: Time window in seconds
            exempt_paths: Paths to exempt from rate limiting
        """
        super().__init__(app)
        self.limiter = RateLimiter(rate=rate, window=window)
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request.
        
        Args:
            request: HTTP request
            
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For first (for proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct client
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply rate limiting.
        
        Args:
            request: HTTP request
            call_next: Next middleware
            
        Returns:
            HTTP response or 429 if rate limited
        """
        # Skip exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        if not self.limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "detail": "Rate limit exceeded. Please try again later.",
                },
                headers={"Retry-After": str(self.limiter.window)},
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = self.limiter.get_remaining(client_ip)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.rate)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.limiter.window)

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and sanitize inputs."""

    PROTECTED_METHODS = ["POST", "PUT", "PATCH"]

    async def dispatch(self, request: Request, call_next) -> Response:
        """Validate request inputs.
        
        Args:
            request: HTTP request
            call_next: Next middleware
            
        Returns:
            HTTP response or 400 if validation fails
        """
        # Check query parameters
        for key, value in request.query_params.items():
            if not InputValidator.is_safe(value):
                logger.warning(
                    f"Suspicious query parameter detected: {key}={value}"
                )
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid input format"},
                )

        # Check body for POST/PUT/PATCH
        if request.method in self.PROTECTED_METHODS:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode()
                    if not InputValidator.is_safe(body_str):
                        logger.warning(
                            f"Suspicious body detected in {request.method} request"
                        )
                        return JSONResponse(
                            status_code=400,
                            content={"error": "Invalid input format"},
                        )
            except Exception as e:
                logger.error(f"Error validating request body: {e}")

        return await call_next(request)


def setup_security(app, config):
    """Setup security middleware for FastAPI app.
    
    Args:
        app: FastAPI application
        config: Configuration object with security settings
    """
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        rate=config.RATE_LIMIT_REQUESTS,
        window=config.RATE_LIMIT_WINDOW,
    )

    # Add input validation
    app.add_middleware(InputValidationMiddleware)

    # Add security headers (should be last)
    app.add_middleware(SecurityHeadersMiddleware)

    logger.info("Security middleware configured")
