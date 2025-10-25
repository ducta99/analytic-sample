# Cryptocurrency Analytics Dashboard - Architecture Documentation

## 1. System Overview

The Cryptocurrency Analytics Dashboard is a microservices-based real-time analytics platform built with a modern, scalable architecture. The system ingests real-time cryptocurrency data from multiple exchanges, performs advanced analytics, and presents insights through a reactive web dashboard.

### Key Components

```
┌─────────────────────────────────────────────────┐
│              Frontend (React/Next.js)           │
│         - Dashboard, Portfolio, Analytics       │
│         - Real-time WebSocket updates           │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         API Gateway (FastAPI)                   │
│  - Request routing and validation               │
│  - Rate limiting and auth middleware            │
│  - Prometheus metrics collection                │
│  - Request ID tracking (distributed tracing)    │
└─┬──────────────────────────────────────────────┬┘
  │                                               │
  ▼                                               ▼
┌────────────────────────┐  ┌───────────────────────┐
│  Microservices Layer   │  │  Message Queue        │
├────────────────────────┤  ├───────────────────────┤
│ • User Service         │  │ Kafka                 │
│ • Market Data Service  │  │ (price_updates,       │
│ • Analytics Service    │◄─┤  sentiment_updates)   │
│ • Sentiment Service    │  │                       │
│ • Portfolio Service    │  │                       │
└────┬─────────┬─────────┘  └───────────────────────┘
     │         │
     └────┬────┘
          │
    ┌─────▼──────────────────────┐
    │   Data Layer               │
    ├────────────────────────────┤
    │ • PostgreSQL (Primary DB)  │
    │ • Redis (Cache)            │
    │ • Kafka (Event Stream)     │
    └────────────────────────────┘

    ┌─────────────────────────────┐
    │  Monitoring & Observability │
    ├─────────────────────────────┤
    │ • Prometheus (Metrics)      │
    │ • Grafana (Dashboards)      │
    │ • Loki (Log Aggregation)    │
    └─────────────────────────────┘
```

## 2. Microservices Architecture

### 2.1 API Gateway

**Purpose**: Central entry point for all requests

**Responsibilities**:
- Request routing to appropriate microservices
- JWT authentication and authorization
- Rate limiting (token bucket algorithm)
- Request validation and sanitization
- Error handling and standardized responses
- Prometheus metrics collection
- Request ID tracking for distributed tracing
- CORS configuration

**Technology**: FastAPI, Python 3.11+

**Key Endpoints**:
```
POST   /api/users/register          - User registration
POST   /api/users/login             - User authentication
POST   /api/users/refresh           - Token refresh
GET    /api/market/*                - Market data routes
GET    /api/analytics/*             - Analytics routes
GET    /api/sentiment/*             - Sentiment routes
WS     /ws/*                        - WebSocket connections
GET    /health                      - Health check
GET    /metrics                     - Prometheus metrics
```

### 2.2 User Service

**Purpose**: Authentication, authorization, and user profile management

**Responsibilities**:
- User registration with email validation
- User authentication with JWT
- Password hashing (bcrypt, 12+ rounds)
- Refresh token management
- User profile management
- Preference storage

**Database**: PostgreSQL

**Key Tables**:
- `users` - User accounts and authentication
- `user_preferences` - User settings (theme, notifications, etc.)

### 2.3 Market Data Service

**Purpose**: Real-time price data ingestion from cryptocurrency exchanges

**Responsibilities**:
- WebSocket connections to Binance and Coinbase
- Price data normalization
- Kafka producer for price updates
- Redis caching of latest prices
- Automatic reconnection with exponential backoff

**Data Sources**:
- Binance WebSocket API
- Coinbase WebSocket API

**Kafka Topics**: `price_updates`

**Cache Strategy**: Redis TTL 5-10 seconds

### 2.4 Analytics Service

**Purpose**: Real-time computation of technical indicators and metrics

**Responsibilities**:
- Kafka consumer for price data
- Moving Average calculations (SMA, EMA)
- Volatility computation (standard deviation)
- Correlation analysis between coins
- Results caching in Redis
- REST API for metric retrieval

**Calculations**:
- **SMA**: Simple arithmetic mean over N periods
- **EMA**: Exponential moving average with K = 2/(N+1)
- **Volatility**: Standard deviation of price changes
- **Correlation**: Pearson correlation coefficient

**Kafka Topics**: `price_updates` (consumer)

**Cache Strategy**: Redis TTL 1-5 minutes

### 2.5 Sentiment Service

**Purpose**: NLP-based sentiment analysis of cryptocurrency news and social media

**Responsibilities**:
- News ingestion from NewsAPI
- Sentiment classification using Hugging Face transformers
- Kafka producer for sentiment scores
- Trend tracking and storage
- REST API for sentiment retrieval

**Data Sources**:
- NewsAPI (crypto news articles)

**NLP Model**: DistilBERT fine-tuned on sentiment classification

**Kafka Topics**: `sentiment_updates` (producer)

**Cache Strategy**: Redis TTL 5 minutes

### 2.6 Portfolio Service

**Purpose**: Portfolio management and performance tracking

**Responsibilities**:
- Portfolio CRUD operations
- Asset management (add/remove/update)
- Performance calculations (value, gain/loss, ROI)
- Watchlist management
- Historical tracking

**Database**: PostgreSQL

**Key Tables**:
- `portfolios` - Portfolio metadata
- `portfolio_assets` - Asset holdings
- `portfolio_history` - Historical snapshots
- `watchlist` - Tracked coins

## 3. Data Layer

### 3.1 PostgreSQL Database

**Schema**:

```sql
-- Users and authentication
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true
);

-- Portfolio management
CREATE TABLE portfolios (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portfolio_assets (
  id SERIAL PRIMARY KEY,
  portfolio_id INTEGER REFERENCES portfolios(id),
  coin_id VARCHAR(50) NOT NULL,
  quantity DECIMAL(20,8) NOT NULL,
  purchase_price DECIMAL(20,8) NOT NULL,
  purchase_date TIMESTAMP NOT NULL,
  INDEX (portfolio_id, coin_id)
);

-- Price history (time-series)
CREATE TABLE prices (
  id SERIAL PRIMARY KEY,
  coin_id VARCHAR(50) NOT NULL,
  price DECIMAL(20,8) NOT NULL,
  volume DECIMAL(20,2),
  timestamp TIMESTAMP NOT NULL,
  INDEX (coin_id, timestamp)
);

-- Sentiment data
CREATE TABLE sentiments (
  id SERIAL PRIMARY KEY,
  coin_id VARCHAR(50) NOT NULL,
  score FLOAT,
  positive_pct FLOAT,
  negative_pct FLOAT,
  neutral_pct FLOAT,
  timestamp TIMESTAMP NOT NULL,
  INDEX (coin_id, timestamp)
);
```

### 3.2 Redis Cache

**Cache Keys Strategy**:

| Key Pattern | TTL | Value |
|---|---|---|
| `price:{coin_id}` | 5-10s | Current price |
| `analytics:{metric}:{coin_id}:{period}` | 1-5min | Metric value |
| `sentiment:{coin_id}` | 5min | Sentiment score |
| `portfolio:{user_id}:{portfolio_id}` | 5min | Portfolio data |
| `user:prefs:{user_id}` | 10min | User preferences |

**Connection**: Persistent pool with 10-50 connections

### 3.3 Kafka Message Queue

**Topics**:

| Topic | Partitions | Replication | Retention | Purpose |
|---|---|---|---|---|
| `price_updates` | 12 | 3 | 7 days | Market data events |
| `sentiment_updates` | 6 | 3 | 7 days | Sentiment analysis |

**Message Format**:

```json
{
  "coin_id": "bitcoin",
  "price": 45250.50,
  "volume": 1234567.89,
  "source": "binance",
  "timestamp": "2025-10-25T10:30:15Z"
}
```

## 4. Frontend Architecture

### 4.1 Technology Stack

- **Framework**: Next.js 14 with React 18
- **Styling**: TailwindCSS + custom CSS
- **State Management**: Redux Toolkit + Zustand
- **API Client**: Axios with interceptors
- **Charting**: Recharts
- **Forms**: React Hook Form + Zod validation
- **Real-time**: WebSocket API

### 4.2 Directory Structure

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Dashboard
│   │   ├── portfolio/
│   │   ├── analytics/
│   │   ├── sentiment/
│   │   └── auth/
│   ├── components/               # Reusable components
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── PriceChart.tsx
│   │   ├── PortfolioCard.tsx
│   │   └── common/
│   ├── hooks/                    # Custom React hooks
│   │   ├── usePrice.ts
│   │   ├── useWebSocket.ts
│   │   └── useAuth.ts
│   ├── context/                  # React Context
│   │   └── AuthContext.tsx
│   ├── store/                    # Redux store
│   │   ├── slices/
│   │   └── index.ts
│   ├── utils/                    # Utilities
│   │   ├── api-client.ts
│   │   ├── websocket.ts
│   │   └── format.ts
│   ├── types/                    # TypeScript types
│   │   └── index.ts
│   └── globals.css               # Global styles
├── public/                        # Static assets
├── next.config.js                # Next.js config
├── tailwind.config.js            # Tailwind config
├── tsconfig.json                 # TypeScript config
└── package.json
```

### 4.3 Key Features

**Dashboard**:
- Real-time price display
- Top gainers/losers
- Market statistics
- Quick action buttons

**Portfolio**:
- Portfolio listing
- Asset allocation pie chart
- Performance metrics
- Add/edit/delete assets
- Historical performance chart

**Analytics**:
- Technical indicators (SMA, EMA, Volatility)
- Coin correlation heatmap
- Multi-timeframe support
- Interactive charts

**Sentiment**:
- Sentiment scores by coin
- Sentiment trend visualization
- News feed integration
- Social media sentiment

## 5. Communication Patterns

### 5.1 Synchronous (REST API)

**Flow**:
```
Frontend → API Gateway → Microservice → PostgreSQL
                    ↓
                  Cache (Redis)
```

**Example**:
```bash
GET /api/portfolio/{id}/performance
Response: { total_value, gain_loss, roi_percentage }
```

### 5.2 Asynchronous (Kafka)

**Flow**:
```
Market Data Service → Kafka (price_updates)
                        ↓
                    Analytics Service → PostgreSQL + Redis
                        ↓
                    API Gateway (WebSocket)
                        ↓
                    Frontend (Real-time)
```

### 5.3 Real-time (WebSocket)

**Connection**:
```
Frontend →(WebSocket)→ API Gateway ↔ Market Data Service
                              ↓
                            Redis
```

**Message Format**:
```json
{
  "type": "price_update",
  "coin_id": "bitcoin",
  "price": 45250.50,
  "timestamp": "2025-10-25T10:30:15Z"
}
```

## 6. Security Architecture

### 6.1 Authentication

- **Method**: JWT (JSON Web Tokens)
- **Algorithm**: HS256
- **Access Token TTL**: 1 hour
- **Refresh Token TTL**: 7 days
- **Signature**: HMAC with secret key

### 6.2 Authorization

- **Pattern**: Role-Based Access Control (RBAC)
- **Roles**: User, Admin
- **Enforcement**: Middleware on each service

### 6.3 Data Protection

- **Passwords**: bcrypt (12+ rounds)
- **Secrets**: Environment variables (no hardcoded)
- **Transport**: HTTPS/TLS
- **Database**: Encrypted at-rest (optional)

### 6.4 Validation

- **Input**: Pydantic schemas on all endpoints
- **SQL**: Parameterized queries (ORM)
- **XSS**: Content Security Policy headers
- **CSRF**: Token validation for state-changing operations

## 7. Monitoring & Observability

### 7.1 Metrics (Prometheus)

**Key Metrics**:
- HTTP request count/latency
- Error rates by status code
- Database query performance
- Cache hit/miss rates
- Kafka lag
- System resources (CPU, memory, disk)

**Scrape Interval**: 15 seconds
**Retention**: 15 days

### 7.2 Dashboards (Grafana)

**Available Dashboards**:
1. **API Gateway & Application Metrics**
   - Response time (p95, p99)
   - Request rate by endpoint
   - Error rate and distribution
   - Rate limiting hits

2. **Infrastructure & System Metrics**
   - Node health status
   - CPU, Memory, Disk usage
   - Network I/O
   - Container metrics

3. **Business & Data Pipeline Metrics**
   - Price update rate
   - Sentiment score rate
   - Portfolio calculations
   - Cache performance
   - Kafka throughput

### 7.3 Logging (Loki)

**Log Format**: Structured JSON

```json
{
  "timestamp": "2025-10-25T10:30:15Z",
  "level": "INFO",
  "service": "api-gateway",
  "request_id": "uuid-here",
  "message": "User login successful",
  "user_id": "123",
  "duration_ms": 125
}
```

**Retention**: 30 days

### 7.4 Alerting

**Alert Rules**:
- Service down (1min threshold)
- High error rate (> 1%)
- High latency (p95 > 500ms)
- Database connection pool exhausted
- Cache eviction rate high
- Kafka consumer lag > 10000
- Disk usage > 85%
- Memory usage > 90%

**Notification**: Slack/PagerDuty integration

## 8. Deployment Architecture

### 8.1 Kubernetes Deployment

**Namespace**: `crypto-analytics`

**Replicas**:
| Service | Min | Max | CPU | Memory |
|---|---|---|---|---|
| API Gateway | 2 | 10 | 500m | 512Mi |
| User Service | 2 | 5 | 500m | 512Mi |
| Market Data | 2 | 10 | 1000m | 1Gi |
| Analytics | 2 | 10 | 2000m | 2Gi |
| Sentiment | 1 | 5 | 1000m | 2Gi |
| Frontend | 2 | 10 | 200m | 256Mi |

**Databases**:
- PostgreSQL: StatefulSet with persistent volumes
- Redis: StatefulSet with AOF persistence
- Kafka: StatefulSet with 3 brokers

### 8.2 CI/CD Pipeline

**GitHub Actions**:
1. Run linting (ESLint, Pylint)
2. Run unit tests
3. Build Docker images
4. Push to registry
5. Deploy to staging
6. Run smoke tests
7. Deploy to production

## 9. Performance Targets

| Metric | Target | Priority |
|---|---|---|
| API p95 latency | < 100ms | High |
| API p99 latency | < 200ms | High |
| Error rate | < 0.5% | Critical |
| Page load | < 3s | High |
| Real-time update latency | < 2s | High |
| Uptime SLA | 99.5% | Critical |
| Cache hit rate | > 80% | Medium |

## 10. Scaling Considerations

### Horizontal Scaling
- Stateless microservices: Auto-scale via load metrics
- Kafka consumers: Consumer groups for parallelism
- Frontend: Load balancer with multiple instances

### Vertical Scaling
- PostgreSQL: Higher memory/CPU for query optimization
- Redis: Memory increase for larger datasets
- Services: CPU/memory increase for CPU-bound operations

### Database Scaling
- PostgreSQL: Read replicas for analytics queries
- Partitioning: Time-series data (prices) by month
- Archival: Old data to separate storage

## 11. Disaster Recovery

**Backup Strategy**:
- PostgreSQL: Daily incremental backups (30-day retention)
- Redis: AOF persistence with daily snapshots
- Kafka: Replication factor 3 (automatic recovery)

**RTO/RPO**:
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 15 minutes

---

**Last Updated**: October 25, 2025  
**Version**: 1.0.0  
**Status**: Production Ready
