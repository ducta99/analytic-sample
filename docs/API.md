# API Documentation

**API Gateway**: `http://localhost:8000`  
**Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)  
**Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

## Table of Contents

1. [Authentication](#authentication)
2. [Market Data](#market-data)
3. [Analytics](#analytics)
4. [Sentiment](#sentiment)
5. [Portfolio](#portfolio)
6. [WebSocket](#websocket)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)

---

## Authentication

All endpoints except health checks require JWT authentication. Include the token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Register User

Create a new user account.

**Endpoint**: `POST /api/users/register`

**Rate Limit**: 5 requests per minute per IP

**Request Body**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_expires_in": 3600
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "email": "Invalid email"
    }
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

**Error Response** (409 Conflict):
```json
{
  "success": false,
  "error": {
    "code": "USER_EXISTS",
    "message": "User with this email already exists"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

### Login User

Authenticate and receive JWT tokens.

**Endpoint**: `POST /api/users/login`

**Rate Limit**: 5 requests per minute per IP

**Request Body**:
```json
{
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_expires_in": 3600
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

**Error Response** (401 Unauthorized):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

### Refresh Token

Get a new access token using a refresh token.

**Endpoint**: `POST /api/users/refresh`

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_expires_in": 3600
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

**Error Response** (401 Unauthorized):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Refresh token is invalid or expired"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

## Market Data

### Get Current Price

Retrieve the current price of a cryptocurrency.

**Endpoint**: `GET /api/market/price/{coin_id}`

**Authentication**: Required

**Parameters**:
- `coin_id` (path, required): Cryptocurrency ID (e.g., 'bitcoin', 'ethereum')

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "coin_id": "bitcoin",
    "symbol": "BTC",
    "price": 45250.50,
    "volume": 28500000000,
    "price_change_pct": 2.45,
    "timestamp": "2025-10-25T10:30:15Z"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:15Z"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "COIN_NOT_FOUND",
    "message": "Cryptocurrency with ID 'bitcoin' not found"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:15Z"
  }
}
```

---

### Get Multiple Prices

Retrieve prices for multiple cryptocurrencies at once.

**Endpoint**: `GET /api/market/prices`

**Authentication**: Required

**Query Parameters**:
- `coins` (required): Comma-separated list of coin IDs (e.g., 'bitcoin,ethereum,cardano')

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "coin_id": "bitcoin",
      "symbol": "BTC",
      "price": 45250.50,
      "volume": 28500000000,
      "price_change_pct": 2.45,
      "timestamp": "2025-10-25T10:30:15Z"
    },
    {
      "coin_id": "ethereum",
      "symbol": "ETH",
      "price": 2350.75,
      "volume": 15200000000,
      "price_change_pct": 1.82,
      "timestamp": "2025-10-25T10:30:15Z"
    }
  ],
  "meta": {
    "timestamp": "2025-10-25T10:30:15Z",
    "count": 2
  }
}
```

---

## Analytics

### Get Moving Average

Calculate Simple Moving Average (SMA) or Exponential Moving Average (EMA) for a cryptocurrency.

**Endpoint**: `GET /api/analytics/moving-average/{coin_id}`

**Authentication**: Required

**Parameters**:
- `coin_id` (path, required): Cryptocurrency ID
- `period` (query, optional): Number of periods (default: 20)
- `method` (query, optional): 'sma' or 'ema' (default: 'sma')

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "coin_id": "bitcoin",
    "method": "sma",
    "period": 20,
    "current_value": 44875.30,
    "values": [
      {
        "timestamp": "2025-10-25T09:00:00Z",
        "value": 44500.00
      },
      {
        "timestamp": "2025-10-25T09:30:00Z",
        "value": 44600.50
      }
    ]
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

### Get Volatility

Calculate price volatility (standard deviation) for a cryptocurrency.

**Endpoint**: `GET /api/analytics/volatility/{coin_id}`

**Authentication**: Required

**Parameters**:
- `coin_id` (path, required): Cryptocurrency ID
- `period` (query, optional): Number of periods (default: 20)

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "coin_id": "bitcoin",
    "period": 20,
    "volatility": 0.0245,
    "volatility_pct": 2.45,
    "min_price": 44200.00,
    "max_price": 46100.00,
    "avg_price": 45250.50
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

### Get Correlation

Calculate price correlation coefficient between two cryptocurrencies.

**Endpoint**: `GET /api/analytics/correlation`

**Authentication**: Required

**Query Parameters**:
- `coin1` (required): First cryptocurrency ID
- `coin2` (required): Second cryptocurrency ID

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "coin_1": "bitcoin",
    "coin_2": "ethereum",
    "correlation": 0.85,
    "period": 30,
    "interpretation": "Strong positive correlation"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

## Sentiment

### Get Sentiment Score

Retrieve sentiment analysis for a cryptocurrency.

**Endpoint**: `GET /api/sentiment/{coin_id}`

**Authentication**: Required

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "coin_id": "bitcoin",
    "overall_score": 0.65,
    "positive_pct": 72,
    "negative_pct": 18,
    "neutral_pct": 10,
    "articles_analyzed": 150,
    "trend": "improving"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

### Get Sentiment Trend

Retrieve sentiment trend over time.

**Endpoint**: `GET /api/sentiment/{coin_id}/trend`

**Authentication**: Required

**Query Parameters**:
- `days` (optional): Number of days to retrieve (default: 7)

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "coin_id": "bitcoin",
    "trend_data": [
      {
        "date": "2025-10-19",
        "score": 0.45,
        "positive_pct": 60,
        "negative_pct": 25,
        "neutral_pct": 15
      },
      {
        "date": "2025-10-20",
        "score": 0.55,
        "positive_pct": 68,
        "negative_pct": 22,
        "neutral_pct": 10
      }
    ]
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

### Get News Feed

Retrieve news articles for a cryptocurrency.

**Endpoint**: `GET /api/sentiment/news/{coin_id}`

**Authentication**: Required

**Query Parameters**:
- `limit` (optional): Maximum number of articles (default: 10, max: 100)
- `sort` (optional): 'recent' or 'relevant' (default: 'recent')

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "id": "article_123",
      "title": "Bitcoin Reaches New High",
      "description": "Bitcoin price surpassed previous resistance levels...",
      "url": "https://news.example.com/bitcoin-high",
      "source": "CryptoNews",
      "published_at": "2025-10-25T09:30:00Z",
      "sentiment_score": 0.75
    }
  ],
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z",
    "count": 1
  }
}
```

---

## Portfolio

### Create Portfolio

Create a new portfolio for the authenticated user.

**Endpoint**: `POST /api/portfolio`

**Authentication**: Required

**Request Body**:
```json
{
  "name": "Main Portfolio",
  "description": "My primary investment portfolio"
}
```

**Success Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "portfolio_id": 1,
    "user_id": 1,
    "name": "Main Portfolio",
    "description": "My primary investment portfolio",
    "created_at": "2025-10-25T10:30:00Z"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

### Get Portfolio

Retrieve details of a specific portfolio.

**Endpoint**: `GET /api/portfolio/{portfolio_id}`

**Authentication**: Required

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "portfolio_id": 1,
    "user_id": 1,
    "name": "Main Portfolio",
    "assets": [
      {
        "coin_id": "bitcoin",
        "symbol": "BTC",
        "quantity": 0.5,
        "purchase_price": 40000.00,
        "current_price": 45250.50,
        "purchase_date": "2025-09-01T00:00:00Z"
      }
    ],
    "performance": {
      "total_value": 22625.25,
      "total_cost": 20000.00,
      "gain_loss": 2625.25,
      "gain_loss_pct": 13.13,
      "roi_pct": 13.13
    },
    "created_at": "2025-09-01T00:00:00Z"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

### Add Asset to Portfolio

Add a cryptocurrency asset to a portfolio.

**Endpoint**: `POST /api/portfolio/{portfolio_id}/assets`

**Authentication**: Required

**Request Body**:
```json
{
  "coin_id": "bitcoin",
  "quantity": 0.5,
  "purchase_price": 40000.00,
  "purchase_date": "2025-09-01T00:00:00Z"
}
```

**Success Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "asset_id": 1,
    "portfolio_id": 1,
    "coin_id": "bitcoin",
    "quantity": 0.5,
    "purchase_price": 40000.00,
    "purchase_date": "2025-09-01T00:00:00Z"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

### Get Portfolio Performance

Retrieve performance metrics for a portfolio.

**Endpoint**: `GET /api/portfolio/{portfolio_id}/performance`

**Authentication**: Required

**Success Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "portfolio_id": 1,
    "total_value": 22625.25,
    "total_cost": 20000.00,
    "gain_loss": 2625.25,
    "gain_loss_pct": 13.13,
    "roi_pct": 13.13,
    "last_updated": "2025-10-25T10:30:00Z"
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

## WebSocket

Connect to real-time updates via WebSocket.

### Connection URL

```
ws://localhost:8000/ws?token=<access_token>
```

### Price Updates Stream

Subscribe to real-time price updates for specific coins.

**Message Type**: `subscribe`

**Request**:
```json
{
  "action": "subscribe",
  "channel": "prices",
  "coins": ["bitcoin", "ethereum"]
}
```

**Response** (Price Update):
```json
{
  "type": "price_update",
  "data": {
    "coin_id": "bitcoin",
    "symbol": "BTC",
    "price": 45250.50,
    "volume": 28500000000,
    "price_change_pct": 2.45,
    "timestamp": "2025-10-25T10:30:15Z"
  },
  "timestamp": "2025-10-25T10:30:15Z",
  "message_id": "msg_abc123"
}
```

---

### Sentiment Updates Stream

Subscribe to sentiment updates.

**Message Type**: `subscribe`

**Request**:
```json
{
  "action": "subscribe",
  "channel": "sentiment",
  "coins": ["bitcoin", "ethereum"]
}
```

**Response** (Sentiment Update):
```json
{
  "type": "sentiment_update",
  "data": {
    "coin_id": "bitcoin",
    "score": 0.65,
    "positive_pct": 72,
    "negative_pct": 18,
    "neutral_pct": 10
  },
  "timestamp": "2025-10-25T10:30:15Z",
  "message_id": "msg_def456"
}
```

---

### Portfolio Updates Stream

Subscribe to portfolio updates.

**Message Type**: `subscribe`

**Request**:
```json
{
  "action": "subscribe",
  "channel": "portfolio",
  "portfolio_id": 1
}
```

**Response** (Portfolio Update):
```json
{
  "type": "portfolio_update",
  "data": {
    "portfolio_id": 1,
    "total_value": 22625.25,
    "total_cost": 20000.00,
    "gain_loss": 2625.25,
    "roi_pct": 13.13
  },
  "timestamp": "2025-10-25T10:30:15Z",
  "message_id": "msg_ghi789"
}
```

---

## Error Handling

All error responses follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field_name": "Specific error detail"
    }
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

### HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input parameters |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Access denied (insufficient permissions) |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |
| 502 | Bad Gateway | Downstream service unavailable |
| 503 | Service Unavailable | Service temporarily down |

### Error Codes

- `VALIDATION_ERROR` - Invalid input parameters
- `AUTHENTICATION_ERROR` - Authentication failed
- `AUTHORIZATION_ERROR` - Authorization failed
- `NOT_FOUND` - Resource not found
- `RATE_LIMIT_ERROR` - Rate limit exceeded
- `SERVICE_UNAVAILABLE` - Service temporarily unavailable
- `INVALID_TOKEN` - JWT token is invalid or expired
- `USER_EXISTS` - User with this email already exists
- `INVALID_CREDENTIALS` - Email or password is incorrect
- `COIN_NOT_FOUND` - Cryptocurrency not found

---

## Rate Limiting

Rate limits vary by endpoint:

| Endpoint | Limit |
|----------|-------|
| `/api/users/register` | 5 req/min per IP |
| `/api/users/login` | 5 req/min per IP |
| `/api/market/*` | 100 req/min per user |
| `/api/analytics/*` | 100 req/min per user |
| `/api/sentiment/*` | 100 req/min per user |
| `/api/portfolio/*` | 100 req/min per user |

When rate limited, you'll receive:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_ERROR",
    "message": "Rate limit exceeded. Please try again later.",
    "details": {
      "retry_after": 60
    }
  },
  "meta": {
    "timestamp": "2025-10-25T10:30:00Z"
  }
}
```

---

## Examples

### Example 1: Complete User Registration and Login Flow

```bash
# Register
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepass123"
  }'

# Login
curl -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123"
  }'

# Get prices using token
curl -X GET 'http://localhost:8000/api/market/prices?coins=bitcoin,ethereum' \
  -H "Authorization: Bearer <access_token>"
```

---

### Example 2: Portfolio Management

```bash
# Create portfolio
curl -X POST http://localhost:8000/api/portfolio \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Portfolio"
  }'

# Add asset to portfolio
curl -X POST http://localhost:8000/api/portfolio/1/assets \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "coin_id": "bitcoin",
    "quantity": 0.5,
    "purchase_price": 40000.00,
    "purchase_date": "2025-09-01T00:00:00Z"
  }'

# Get portfolio with performance
curl -X GET http://localhost:8000/api/portfolio/1 \
  -H "Authorization: Bearer <access_token>"
```

---

### Example 3: Analytics and Technical Indicators

```bash
# Get moving average
curl -X GET 'http://localhost:8000/api/analytics/moving-average/bitcoin?period=20&method=sma' \
  -H "Authorization: Bearer <access_token>"

# Get volatility
curl -X GET 'http://localhost:8000/api/analytics/volatility/bitcoin?period=20' \
  -H "Authorization: Bearer <access_token>"

# Get correlation
curl -X GET 'http://localhost:8000/api/analytics/correlation?coin1=bitcoin&coin2=ethereum' \
  -H "Authorization: Bearer <access_token>"
```

---

### Example 4: WebSocket Real-Time Updates

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws?token=<access_token>');

// Subscribe to price updates
ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'prices',
    coins: ['bitcoin', 'ethereum']
  }));
};

// Receive price updates
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Price update:', message.data);
};

// Error handling
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

---

**Last Updated**: October 25, 2025  
**Version**: 1.0.0
