# CORS and Security Headers Configuration

Comprehensive guide for configuring Cross-Origin Resource Sharing (CORS) and security headers across the microservices architecture.

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** January 2025

## Table of Contents

1. [CORS Configuration](#cors-configuration)
2. [Security Headers](#security-headers)
3. [API Gateway Setup](#api-gateway-setup)
4. [Service-Level Configuration](#service-level-configuration)
5. [Testing & Validation](#testing--validation)
6. [Troubleshooting](#troubleshooting)

---

## CORS Configuration

### 1. CORS Basics

**What is CORS?**
Cross-Origin Resource Sharing controls which domains can access your API.

```
Frontend Domain: https://analytics.example.com
API Domain: https://api.example.com

Browser Request:
- Origin: https://analytics.example.com
- Path: GET /api/market/prices

Server Response Headers:
- Access-Control-Allow-Origin: https://analytics.example.com
- Access-Control-Allow-Methods: GET, POST, PUT, DELETE
- Access-Control-Allow-Headers: Content-Type, Authorization

Browser: ✅ Request allowed (origins match CORS policy)
```

### 2. Allowed Origins Configuration

**Production Environment:**

```python
# api-gateway/app/config.py

from typing import List

class CORSConfig:
    """CORS configuration for production and development."""
    
    # Production allowed origins
    PRODUCTION_ORIGINS = [
        "https://analytics.example.com",          # Main frontend domain
        "https://www.analytics.example.com",      # With www
        "https://app.analytics.example.com",      # Subdomain
    ]
    
    # Staging allowed origins
    STAGING_ORIGINS = [
        "https://staging.analytics.example.com",
        "https://dev.analytics.example.com",
    ]
    
    # Development allowed origins
    DEVELOPMENT_ORIGINS = [
        "http://localhost:3000",      # Frontend dev server
        "http://localhost:8080",      # Alternative port
        "http://127.0.0.1:3000",      # IPv4 localhost
    ]
    
    # Get allowed origins based on environment
    @staticmethod
    def get_allowed_origins(environment: str) -> List[str]:
        """
        Get allowed origins based on environment.
        
        Args:
            environment: 'production', 'staging', or 'development'
        
        Returns:
            List of allowed origin URLs
        """
        if environment == "production":
            return CORSConfig.PRODUCTION_ORIGINS
        elif environment == "staging":
            return CORSConfig.STAGING_ORIGINS + CORSConfig.PRODUCTION_ORIGINS
        else:  # development
            return (
                CORSConfig.DEVELOPMENT_ORIGINS +
                CORSConfig.STAGING_ORIGINS +
                CORSConfig.PRODUCTION_ORIGINS
            )
```

### 3. FastAPI CORS Middleware

**api-gateway/app/main.py:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORSConfig
import os

app = FastAPI(
    title="Cryptocurrency Analytics API Gateway",
    description="Main API gateway for microservices",
    version="1.0.0"
)

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Get allowed origins
allowed_origins = CORSConfig.get_allowed_origins(ENVIRONMENT)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,          # Specific origins only
    allow_credentials=True,                 # Allow cookies/auth headers
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[                         # Allowed request headers
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=[                        # Headers exposed to frontend
        "X-Total-Count",                    # Pagination
        "X-Page-Number",
        "X-Page-Size",
        "RateLimit-Limit",                  # Rate limiting info
        "RateLimit-Remaining",
        "RateLimit-Reset",
        "X-Request-ID",                     # Request tracing
        "X-Correlation-ID",
    ],
    max_age=3600,                          # Preflight cache: 1 hour
)

# ✅ Verify CORS configuration
print(f"[CORS] Environment: {ENVIRONMENT}")
print(f"[CORS] Allowed origins: {', '.join(allowed_origins)}")
print(f"[CORS] Max age: 3600 seconds (1 hour)")
```

### 4. Preflight Request Handling

**How preflight works:**

```
Client Browser: OPTIONS /api/market/prices
                Origin: https://analytics.example.com
                
Server Response:
    ✅ Access-Control-Allow-Origin: https://analytics.example.com
    ✅ Access-Control-Allow-Methods: GET, POST, PUT, DELETE
    ✅ Access-Control-Allow-Headers: Content-Type, Authorization
    
Browser: ✅ Preflight passed, now send actual request
```

**FastAPI handles preflight automatically with CORSMiddleware**

### 5. Credentials and Authentication

**CORS with JWT tokens:**

```python
# Frontend code
const response = await fetch('https://api.example.com/api/users/profile', {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    },
    credentials: 'include',  # Include cookies if applicable
});

# Browser preflight:
OPTIONS /api/users/profile
Origin: https://analytics.example.com
Access-Control-Request-Headers: authorization, content-type

# Server response:
Access-Control-Allow-Origin: https://analytics.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true  # ← Important for JWT
```

---

## Security Headers

### 1. Security Headers Overview

| Header | Purpose | Example |
|--------|---------|---------|
| X-Content-Type-Options | Prevent MIME type sniffing | nosniff |
| X-Frame-Options | Prevent clickjacking | DENY |
| X-XSS-Protection | Legacy XSS filter | 1; mode=block |
| Strict-Transport-Security | Force HTTPS | max-age=31536000 |
| Content-Security-Policy | Control resource loading | default-src 'self' |
| Referrer-Policy | Control referrer info | strict-no-referrer |

### 2. FastAPI Security Headers Middleware

**Create middleware file: api-gateway/app/middleware/security_headers.py**

```python
"""
Security headers middleware for all API responses.
Implements industry-standard security headers to protect against common attacks.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Determine environment
        environment = os.getenv("ENVIRONMENT", "development")
        
        # ===== Security Headers =====
        
        # 1. X-Content-Type-Options
        # Prevent MIME type sniffing attacks
        # Tells browser to trust Content-Type header
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 2. X-Frame-Options
        # Prevent clickjacking attacks
        # DENY: Frame cannot be displayed in a frame
        response.headers["X-Frame-Options"] = "DENY"
        
        # 3. X-XSS-Protection
        # Enable XSS protection filter (legacy, modern browsers use CSP)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 4. Referrer-Policy
        # Control how much referrer information is sent
        response.headers["Referrer-Policy"] = "strict-no-referrer"
        
        # 5. Permissions-Policy
        # Control which browser features can be used
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )
        
        # 6. Content-Security-Policy (CSP)
        # Comprehensive XSS and injection protection
        if environment == "production":
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https://api.example.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # More permissive for development
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' http://localhost:* ws://localhost:*; "
                "frame-ancestors 'none'"
            )
        
        response.headers["Content-Security-Policy"] = csp_policy
        
        # 7. Strict-Transport-Security (HSTS)
        # Force HTTPS in production
        if environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; "           # 1 year
                "includeSubDomains; "          # Apply to subdomains
                "preload"                      # HSTS preload list
            )
        else:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        
        # 8. X-Powered-By
        # Remove or spoof (don't reveal tech stack)
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        response.headers["X-Powered-By"] = "CustomFramework/1.0"
        
        # 9. Server
        # Hide or spoof server info
        response.headers["Server"] = "API Gateway/1.0"
        
        # 10. Rate Limit Headers (if using rate limiter)
        # These would be set by rate limiting middleware
        # Examples:
        # RateLimit-Limit: 100
        # RateLimit-Remaining: 99
        # RateLimit-Reset: 1234567890
        
        return response


# ===== Header Examples =====
"""
Production Response Headers:

HTTP/1.1 200 OK
Content-Type: application/json
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-no-referrer
Permissions-Policy: accelerometer=(), camera=(), ...
Content-Security-Policy: default-src 'self'; script-src 'self'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Powered-By: CustomFramework/1.0
Server: API Gateway/1.0

Development Response Headers:

HTTP/1.1 200 OK
Content-Type: application/json
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-no-referrer
Permissions-Policy: accelerometer=(), camera=(), ...
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-eval'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Powered-By: CustomFramework/1.0
Server: API Gateway/1.0
"""
```

### 3. Add Middleware to FastAPI App

**Update api-gateway/app/main.py:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.config import CORSConfig
import os

app = FastAPI(
    title="Cryptocurrency Analytics API Gateway",
    description="Main API gateway for microservices",
    version="1.0.0"
)

# ===== Add Middleware (Order Matters!) =====

# 1. CORS Middleware (before security headers)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
allowed_origins = CORSConfig.get_allowed_origins(ENVIRONMENT)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=[
        "X-Total-Count",
        "RateLimit-Limit",
        "RateLimit-Remaining",
        "RateLimit-Reset",
        "X-Request-ID",
    ],
    max_age=3600,
)

# 2. Security Headers Middleware (after CORS)
app.add_middleware(SecurityHeadersMiddleware)

# 3. Other middleware (logging, error handling, etc.)
```

---

## API Gateway Setup

### 1. Complete API Gateway Configuration

**api-gateway/app/config.py:**

```python
"""
Complete configuration for API Gateway with CORS and security.
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = ENVIRONMENT != "production"
    
    # API Configuration
    API_TITLE = "Cryptocurrency Analytics API Gateway"
    API_DESCRIPTION = "Main API gateway for cryptocurrency analytics microservices"
    API_VERSION = "1.0.0"
    
    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    JWT_REFRESH_EXPIRATION_DAYS = 7
    
    # CORS
    CORS_CONFIG = {
        "production": {
            "origins": [
                "https://analytics.example.com",
                "https://www.analytics.example.com",
            ],
            "credentials": True,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "max_age": 3600,
        },
        "staging": {
            "origins": [
                "https://staging.analytics.example.com",
                "https://dev.analytics.example.com",
                "https://analytics.example.com",
            ],
            "credentials": True,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "max_age": 1800,
        },
        "development": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8080",
            ],
            "credentials": True,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "max_age": 600,
        },
    }
    
    @property
    def cors_origins(self) -> List[str]:
        """Get allowed CORS origins based on environment."""
        return self.CORS_CONFIG.get(self.ENVIRONMENT, {}).get("origins", [])
    
    @property
    def cors_max_age(self) -> int:
        """Get CORS max age based on environment."""
        return self.CORS_CONFIG.get(self.ENVIRONMENT, {}).get("max_age", 3600)
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    
    # Service URLs (internal)
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    MARKET_DATA_SERVICE_URL = os.getenv("MARKET_DATA_SERVICE_URL", "http://market-data-service:8002")
    ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8003")
    SENTIMENT_SERVICE_URL = os.getenv("SENTIMENT_SERVICE_URL", "http://sentiment-service:8004")
    PORTFOLIO_SERVICE_URL = os.getenv("PORTFOLIO_SERVICE_URL", "http://portfolio-service:8005")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# Global settings instance
settings = Settings()
```

### 2. Environment Variables

**Create `.env` file (development):**

```bash
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# JWT
JWT_SECRET=your-development-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Service URLs
USER_SERVICE_URL=http://user-service:8001
MARKET_DATA_SERVICE_URL=http://market-data-service:8002
ANALYTICS_SERVICE_URL=http://analytics-service:8003
SENTIMENT_SERVICE_URL=http://sentiment-service:8004
PORTFOLIO_SERVICE_URL=http://portfolio-service:8005
```

**Create `.env.production` file:**

```bash
# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# JWT
JWT_SECRET=use-secure-random-key-from-secrets-manager
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW_SECONDS=60

# Service URLs (internal network)
USER_SERVICE_URL=http://user-service:8001
MARKET_DATA_SERVICE_URL=http://market-data-service:8002
ANALYTICS_SERVICE_URL=http://analytics-service:8003
SENTIMENT_SERVICE_URL=http://sentiment-service:8004
PORTFOLIO_SERVICE_URL=http://portfolio-service:8005
```

---

## Service-Level Configuration

### 1. Individual Service Security Headers

**Each microservice should also add security headers for defense-in-depth:**

```python
# shared/middleware.py (shared across all services)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os


class ServiceSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers for individual microservices."""
    
    async def dispatch(self, request, call_next) -> Response:
        response = await call_next(request)
        
        # Basic security headers (even for internal services)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-no-referrer"
        
        # Service-level CSP (more restrictive)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'"
        )
        
        return response
```

### 2. Add to Each Service

```python
# user-service/app/main.py
from fastapi import FastAPI
from shared.middleware import ServiceSecurityHeadersMiddleware

app = FastAPI()
app.add_middleware(ServiceSecurityHeadersMiddleware)

# Similar for:
# - market-data-service/app/main.py
# - analytics-service/app/main.py
# - sentiment-service/app/main.py
# - portfolio-service/app/main.py
```

---

## Testing & Validation

### 1. CORS Testing Script

```bash
#!/bin/bash
# scripts/test_cors.sh

echo "=== Testing CORS Configuration ==="

API_URL="http://localhost:8000"
FRONTEND_ORIGIN="http://localhost:3000"

# Test 1: Preflight request
echo -e "\n[Test 1] Preflight OPTIONS request"
curl -i -X OPTIONS \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  "$API_URL/api/market/prices"

# Expected response:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
# Access-Control-Allow-Headers: Content-Type, Authorization

# Test 2: Actual request with auth
echo -e "\n\n[Test 2] Actual GET request with Authentication"
TOKEN="your-jwt-token"
curl -i -X GET \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/users/profile"

# Expected response:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Credentials: true

# Test 3: Invalid origin
echo -e "\n\n[Test 3] Request from invalid origin"
curl -i -X GET \
  -H "Origin: http://evil.example.com" \
  -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/users/profile"

# Expected response:
# No Access-Control-Allow-Origin header (request blocked)

# Test 4: Security headers
echo -e "\n\n[Test 4] Security headers verification"
curl -i -X GET \
  -H "Origin: $FRONTEND_ORIGIN" \
  "$API_URL/health" | grep -E "X-Content-Type-Options|X-Frame-Options|CSP|HSTS"

# Expected response:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Content-Security-Policy: ...
# Strict-Transport-Security: ... (production only)
```

Run tests:
```bash
chmod +x scripts/test_cors.sh
./scripts/test_cors.sh
```

### 2. Python Testing

```python
# tests/test_cors_and_security.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_allowed_origin(client: AsyncClient):
    """Test CORS header for allowed origin."""
    response = await client.options(
        "/api/market/prices",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    assert "GET" in response.headers.get("Access-Control-Allow-Methods", "")


@pytest.mark.asyncio
async def test_cors_disallowed_origin(client: AsyncClient):
    """Test CORS header for disallowed origin."""
    response = await client.options(
        "/api/market/prices",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        }
    )
    
    # Should not include CORS headers for disallowed origin
    assert response.headers.get("Access-Control-Allow-Origin") != "http://evil.example.com"


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    """Test that security headers are present in all responses."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-no-referrer"
    assert "Content-Security-Policy" in response.headers
```

### 3. Browser Console Test

```javascript
// In browser console (from your frontend domain)

// Test 1: Preflight caching
fetch('http://localhost:8000/api/market/prices')
  .then(r => r.json())
  .then(data => console.log('✅ CORS allowed:', data))
  .catch(e => console.error('❌ CORS blocked:', e));

// Test 2: Security headers (check in DevTools Network tab)
// All responses should include:
// - X-Content-Type-Options: nosniff
// - X-Frame-Options: DENY
// - Content-Security-Policy: ...

// Test 3: XSS protection (CSP prevents execution)
// Should NOT execute:
fetch('http://localhost:8000/api/data')
  .then(r => r.text())
  .then(html => {
    // This would violate CSP if it tried to inject scripts
    document.body.innerHTML = html;  // ← CSP would block <script> tags
  });
```

---

## Troubleshooting

### Issue 1: CORS Error - "No 'Access-Control-Allow-Origin' header"

```
Error: The CORS protocol does not allow specifying a wildcard ('*') 
for requests that include credentials (such as cookies or authorization headers).

Solution:
1. Check CORSConfig.get_allowed_origins() returns your frontend URL
2. Verify ENVIRONMENT variable is set correctly
3. Check frontend domain matches exactly (protocol, domain, port)
4. Test with explicit origin in dev tools

# Debug:
curl -H "Origin: http://localhost:3000" -X OPTIONS http://localhost:8000/health
```

### Issue 2: CORS Error - "Credentials mode is 'include' but Access-Control-Allow-Credentials is missing"

```
Error: The value of the 'Access-Control-Allow-Credentials' header 
in the response is '' which must be 'true' when the request's credentials mode is 'include'.

Solution:
1. Ensure CORSMiddleware has allow_credentials=True
2. Frontend must include credentials: 'include' in fetch

# Frontend:
fetch(url, {
  credentials: 'include',  // ← Required
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### Issue 3: CSP Violation - "Refused to load the script"

```
Violation: Refused to load the script 'https://cdn.example.com/lib.js'
because it violates the Content-Security-Policy directive...

Solution:
1. Update CSP policy to allow external script sources
2. Or host scripts locally

# In SecurityHeadersMiddleware, update CSP:
csp_policy = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.example.com; "  # ← Add domain
    ...
)
```

### Issue 4: Preflight Request Blocked

```
Error: CORS policy: Response to preflight request 
doesn't pass access control check

Solution:
1. Check OPTIONS method is included in allow_methods
2. Verify Allow-Headers includes all requested headers
3. Add Access-Control-Allow-Methods header explicitly

# api-gateway/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # ← Include OPTIONS
    ...
)
```

---

## Checklist for Deployment

### Pre-Deployment

- [ ] CORS origins configured for target environment
- [ ] Security headers middleware added to API Gateway
- [ ] Security headers middleware added to all microservices
- [ ] CSP policy tested with all frontend resources
- [ ] HSTS enabled in production
- [ ] JWT token validation working correctly
- [ ] Rate limiting headers configured

### Testing

- [ ] Preflight requests return correct headers
- [ ] Allowed origins can access API
- [ ] Disallowed origins blocked
- [ ] Security headers present in all responses
- [ ] No console CSP violations
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

### Post-Deployment

- [ ] Monitor for CORS errors in logs
- [ ] Monitor for CSP violations
- [ ] Verify security headers present in prod
- [ ] Test from actual frontend domain
- [ ] Monitor error rates

---

## References

- [MDN CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP Security Headers](https://owasp.org/www-project-secure-headers/)
- [CSP Directive Reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)

---

**Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** January 2025
