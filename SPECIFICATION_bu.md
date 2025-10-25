# 🪙 Cryptocurrency Analytics Dashboard - Specification

**Version**: 1.0 | **Date**: October 25, 2025 | **Status**: In Development

---

## 1. System Overview

A microservice-based real-time cryptocurrency analytics platform with:
- Real-time price aggregation from Binance & Coinbase
- Advanced analytics (moving averages, volatility, correlations)
- Sentiment analysis from news sources
- Portfolio tracking and performance analytics
- Enterprise-grade monitoring and logging

---

## 2. Architecture

```
Frontend (React/Next.js)
        ↓ WebSocket/HTTP
    API Gateway (FastAPI)
        ↓
┌───────────────────────────────────────────────┐
│  User Service │ Market Data │ Analytics │ Sentiment │
└───────────────────────────────────────────────┘
        ↓ Async (Kafka)
┌───────────────────────────────────────────────┐
│  Redis Cache  │  PostgreSQL  │  Kafka Queue  │
└───────────────────────────────────────────────┘
```

---

## 3. Backend Services

### 3.1 User Service
- **Purpose**: Authentication, authorization, user management
- **Tech**: FastAPI, PostgreSQL, JWT
- **Key Endpoints**: 
  - `POST /api/users/register`, `POST /api/users/login`
  - `GET/PUT /api/users/{user_id}`
  - `GET/PUT /api/users/{user_id}/preferences`

### 3.2 Market Data Service
- **Purpose**: Real-time price streaming from exchanges
- **Tech**: FastAPI, WebSocket, Kafka Producer
- **Features**: Binance & Coinbase WebSocket, auto-reconnect, price normalization
- **Key Endpoints**: 
  - `GET /api/market/price/{coin_id}`
  - `WS /api/market/stream`
- **Kafka Topic**: `price_updates`

### 3.3 Analytics Service
- **Purpose**: Compute metrics (moving averages, volatility, correlations)
- **Tech**: FastAPI, Kafka Consumer, Pandas, Redis
- **Key Endpoints**:
  - `GET /api/analytics/moving-average/{coin_id}`
  - `GET /api/analytics/volatility/{coin_id}`
  - `GET /api/analytics/correlation?coin_1=X&coin_2=Y`

**Calculations**:
```
SMA = (P1 + P2 + ... + Pn) / n
EMA = P_today × K + EMA_yesterday × (1 - K), where K = 2/(n+1)
Volatility = sqrt(Σ(Price_i - SMA)² / n)
```

### 3.4 Sentiment Service
- **Purpose**: NLP sentiment analysis from news/social media
- **Tech**: FastAPI, Hugging Face Transformers, NewsAPI
- **Features**: Article ingestion, sentiment classification, trend tracking
- **Key Endpoints**:
  - `GET /api/sentiment/{coin_id}`
  - `GET /api/sentiment/{coin_id}/trend`
  - `GET /api/sentiment/news/{coin_id}`
- **Kafka Topic**: `sentiment_updates`

### 3.5 Portfolio Service
- **Purpose**: Portfolio management and performance tracking
- **Tech**: FastAPI, PostgreSQL, Redis
- **Key Endpoints**:
  - `POST/GET /api/portfolio` - Create/list portfolios
  - `POST /api/portfolio/{portfolio_id}/assets` - Add asset
  - `GET /api/portfolio/{portfolio_id}/performance` - Performance metrics
  - `POST/GET /api/watchlist` - Manage watchlists

**Portfolio Performance**:
```
Total Value = Σ(quantity × current_price)
Gain/Loss = Total Value - Total Cost
ROI% = (Gain/Loss / Total Cost) × 100
```

### 3.6 API Gateway
- **Purpose**: Central request router, authentication, rate limiting
- **Tech**: FastAPI, JWT validation, token bucket algorithm
- **Features**: Request routing, CORS, WebSocket upgrade, error standardization
- **Rate Limits**: 100 req/min (general), 5 req/min (auth), 1000 req/min (data)

---

## 4. Frontend Specification

**Tech Stack**: React 18/Next.js 14, TailwindCSS, Recharts, Redux Toolkit

**Pages**:
- `/login`, `/register` - Authentication
- `/dashboard` - Market overview, top gainers/losers, charts
- `/portfolio` - Portfolio management, asset allocation, performance
- `/analytics` - Technical indicators, correlations, trends
- `/sentiment` - Sentiment scores, news feed, trends
- `/watchlist` - Coin watchlist management
- `/profile` - User settings

**Real-Time Updates**:
- Prices: 1-2 second intervals
- Charts: 5-10 second intervals
- Sentiment: 5-minute intervals

**UI/UX**: Dark mode theme, responsive (320px+), Lighthouse score > 90

---

## 5. Data Models

### User
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);
```

### Prices (Time-Series)
```sql
CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    coin_id VARCHAR(50) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,2),
    timestamp TIMESTAMP NOT NULL,
    INDEX (coin_id, timestamp)
);
```

### Portfolios
```sql
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portfolio_assets (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(id),
    coin_id VARCHAR(50) NOT NULL,
    quantity DECIMAL(20,8),
    purchase_price DECIMAL(20,8),
    purchase_date TIMESTAMP
);
```

### Sentiment
```sql
CREATE TABLE sentiments (
    id SERIAL PRIMARY KEY,
    coin_id VARCHAR(50) NOT NULL,
    score FLOAT (-1 to +1),
    positive_pct FLOAT,
    negative_pct FLOAT,
    timestamp TIMESTAMP,
    INDEX (coin_id, timestamp)
);
```

---

## 6. API Response Format

**Success**:
```json
{
  "success": true,
  "data": { /* payload */ },
  "meta": { "timestamp": "2025-10-25T10:30:00Z" }
}
```

**Error**:
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Coin not found"
  }
}
```

**Error Codes**: 400 (Invalid), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 429 (Rate Limited), 500 (Server Error)

---

## 7. Real-Time Communication

**WebSocket Endpoints**:
- `WS /ws/prices?coins=bitcoin,ethereum` - Price updates
- `WS /ws/sentiment?coins=bitcoin,ethereum` - Sentiment updates
- `WS /ws/portfolio/{portfolio_id}` - Portfolio updates

**Message Format**:
```json
{
  "type": "price_update",
  "data": {
    "coin_id": "bitcoin",
    "price": 45250.50,
    "timestamp": "2025-10-25T10:30:15Z"
  }
}
```

**Connection**: Heartbeat every 30s, timeout after 90s inactivity, auto-reconnect, max 50 coins/connection

---

## 8. Caching Strategy

**Redis Cache**:
- Prices: TTL 5-10s
- Analytics: TTL 1-5min
- Sentiment: TTL 5min
- User preferences: TTL 10min
- Portfolios: TTL 5min

**Cache Keys**:
```
price:{coin_id}
analytics:{metric_type}:{coin_id}:{period}
sentiment:{coin_id}
portfolio:{user_id}:{portfolio_id}
```

**Invalidation**: TTL-based, event-based (price updates), manual (admin)

---

## 9. Security

| Requirement | Implementation |
|---|---|
| Authentication | JWT with 7-day refresh tokens |
| Authorization | Role-based access control (User, Admin) |
| Passwords | bcrypt (12+ rounds) |
| Transport | HTTPS/TLS + WSS for WebSocket |
| Data | SQL injection prevention (parameterized queries) |
| API Security | CORS, CSRF tokens, rate limiting |
| Infrastructure | Environment variables, no hardcoded secrets, private DB subnet |

---

## 10. Performance Targets

| Metric | Target |
|---|---|
| GET /prices latency | < 100ms (p95) |
| GET /analytics latency | < 200ms (p95) |
| GET /portfolio latency | < 200ms (p95) |
| API throughput | 10,000 req/s |
| WebSocket connections | 50,000 concurrent |
| Initial page load | < 3s |
| Chart rendering (1000 points) | < 500ms |
| Uptime SLA | 99.5% |

---

## 11. Deployment

**Docker**: Multi-stage builds, non-root execution, health checks

**Kubernetes**:

| Service | Replicas | CPU/Memory |
|---|---|---|
| API Gateway | 3 (2-10) | 500m/512Mi → 1000m/1Gi |
| Market Data | 2 | 1000m/1Gi → 2000m/2Gi |
| Analytics | 3 (2-10) | 2000m/2Gi → 4000m/4Gi |
| User Service | 2 (2-5) | 500m/512Mi → 1000m/1Gi |
| Sentiment | 2 (1-5) | 1000m/2Gi → 2000m/4Gi |
| Frontend | 3 (2-10) | 200m/256Mi → 500m/512Mi |

**Databases**:
- PostgreSQL 14+: Primary-standby, daily incremental backups (30-day retention)
- Redis 7.0+: 32GB memory, AOF persistence, primary-replica
- Kafka 3.5+: 3 brokers, RF=3, 7-day retention, 12-24 partitions/topic

**Monitoring**:
- Prometheus: 15s scrape, 15-day retention
- Grafana: 30s refresh, Slack/PagerDuty alerts
- Loki: 30-day log retention, error rate alerts > 1%

---

## 12. Key Technologies

**Backend**: Python (FastAPI), PostgreSQL, Redis, Kafka, Docker, Kubernetes  
**Frontend**: React/Next.js, TailwindCSS, shadcn/ui, Recharts, Redux  
**Monitoring**: Prometheus, Grafana, Loki, Jaeger  
**APIs**: Binance WebSocket, Coinbase WebSocket, NewsAPI

---

## 13. Service Dependencies

### Startup Order
1. **PostgreSQL** - Primary database
2. **Redis** - Cache layer
3. **Kafka + Zookeeper** - Message queue
4. **User Service** - Authentication foundation
5. **Market Data Service** - Price ingestion
6. **Analytics Service** - Data processing (depends on Kafka)
7. **Sentiment Service** - NLP processing (depends on Kafka)
8. **Portfolio Service** - Depends on User Service
9. **API Gateway** - Routes to all services
10. **Frontend** - Connects to API Gateway

### Inter-Service Communication
```
Frontend → API Gateway → All Services (sync)
Market Data Service → Kafka → Analytics Service (async)
Market Data Service → Kafka → Sentiment Service (async)
All Services → Redis (caching)
All Services → PostgreSQL (persistence)
```

---

## 14. Implementation Milestones

### Phase 1: Foundation (Week 1-2)
- [ ] Project structure & Docker setup
- [ ] Database schema & migrations
- [ ] API Gateway skeleton
- [ ] JWT authentication middleware

**Deliverable**: Local development environment with docker-compose

### Phase 2: Core Services (Week 3-4)
- [ ] User Service implementation
- [ ] Market Data Service (Binance integration)
- [ ] Basic Kafka setup
- [ ] Redis caching layer

**Deliverable**: Real-time price streaming working

### Phase 3: Analytics & Sentiment (Week 5-6)
- [ ] Analytics Service (moving averages, volatility)
- [ ] Sentiment Service (NLP pipeline)
- [ ] Portfolio Service implementation
- [ ] Kafka consumer integration

**Deliverable**: Complete backend microservices

### Phase 4: Frontend (Week 7-8)
- [ ] React/Next.js setup with TailwindCSS
- [ ] Dashboard page with charts
- [ ] Portfolio and analytics pages
- [ ] WebSocket integration

**Deliverable**: Working frontend dashboard

### Phase 5: DevOps & Deployment (Week 9-10)
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Prometheus & Grafana monitoring
- [ ] Production deployment

**Deliverable**: Production-ready deployment

### Phase 6: Testing & Optimization (Week 11-12)
- [ ] Unit & integration tests
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation

**Deliverable**: Release-ready system

---

## 15. Task Breakdown for AI Agents

### User Service Tasks
```
ID: USER-001
Title: Implement User Registration Endpoint
Description: Create POST /api/users/register with email validation, password hashing
Dependencies: PostgreSQL, bcrypt library
Success Criteria:
  - Account created with bcrypt hashing (12+ rounds)
  - Email uniqueness validation
  - Response includes user_id and JWT token
  - Rate limiting: 5 req/min per IP
Files: user_service/routes/auth.py, models/user.py
Tests: test_user_registration.py

---

ID: USER-002
Title: Implement JWT Authentication Middleware
Description: Create middleware for validating JWT tokens on protected routes
Dependencies: PyJWT library, Redis (for token blacklist)
Success Criteria:
  - Validates JWT signature and expiry
  - Returns 401 for invalid/expired tokens
  - Supports refresh token mechanism
Files: api_gateway/middleware/auth.py
Tests: test_jwt_middleware.py
```

### Market Data Service Tasks
```
ID: MARKET-001
Title: Setup Binance WebSocket Connection
Description: Connect to Binance WebSocket API for real-time price updates
Dependencies: websocket library, Kafka
Success Criteria:
  - Connects to binance wss://stream.binance.com:9443/ws/btcusdt
  - Parses JSON messages
  - Auto-reconnect with exponential backoff
  - Publishes to Kafka topic "price_updates"
Files: market_data_service/clients/binance.py
Tests: test_binance_client.py

---

ID: MARKET-002
Title: Implement Market Data Caching
Description: Cache latest prices in Redis with TTL
Dependencies: Redis, Market Data Service
Success Criteria:
  - Cache key format: price:{coin_id}
  - TTL: 5-10 seconds
  - Atomic operations (no race conditions)
Files: market_data_service/cache.py
Tests: test_market_cache.py
```

### Analytics Service Tasks
```
ID: ANALYTICS-001
Title: Implement Moving Average Calculation
Description: Calculate SMA and EMA from price history
Dependencies: Pandas, Kafka Consumer
Success Criteria:
  - SMA calculation: (P1 + P2 + ... + Pn) / n
  - EMA calculation with K = 2/(n+1)
  - Handles missing data gracefully
  - Results cached with TTL 1-5 min
Files: analytics_service/calculations/moving_average.py
Tests: test_moving_average.py

---

ID: ANALYTICS-002
Title: Implement Volatility Calculation
Description: Calculate standard deviation volatility over periods
Dependencies: NumPy, Pandas
Success Criteria:
  - Calculates: sqrt(Σ(Price_i - SMA)² / n)
  - Supports 24h, 7d, 30d periods
  - Caches results in Redis
Files: analytics_service/calculations/volatility.py
Tests: test_volatility.py
```

### Sentiment Service Tasks
```
ID: SENTIMENT-001
Title: Integrate NewsAPI for Article Ingestion
Description: Fetch crypto news articles and store in database
Dependencies: NewsAPI key, PostgreSQL, requests library
Success Criteria:
  - Fetches latest crypto news
  - Filters by coin keywords
  - Stores to DB: id, title, url, source, published_at
  - Runs on schedule (every 1 hour)
Files: sentiment_service/ingestors/newsapi.py
Tests: test_newsapi_ingestor.py

---

ID: SENTIMENT-002
Title: Implement Sentiment Classifier
Description: Use Hugging Face transformers to classify sentiment
Dependencies: transformers library, CUDA (optional)
Success Criteria:
  - Classifies as positive/negative/neutral
  - Score range: -1 (negative) to +1 (positive)
  - Processes articles in batch
  - Caches model in memory
Files: sentiment_service/nlp/classifier.py
Tests: test_sentiment_classifier.py
```

### Portfolio Service Tasks
```
ID: PORTFOLIO-001
Title: Create Portfolio API Endpoints
Description: Implement CRUD for user portfolios
Dependencies: FastAPI, PostgreSQL, Auth middleware
Success Criteria:
  - POST /api/portfolio - create with user_id, name
  - GET /api/portfolio - list user portfolios
  - PUT /api/portfolio/{id} - update name/description
  - DELETE /api/portfolio/{id} - soft delete
Files: portfolio_service/routes/portfolio.py
Tests: test_portfolio_crud.py

---

ID: PORTFOLIO-002
Title: Implement Portfolio Performance Calculation
Description: Calculate total value, gain/loss, ROI
Dependencies: Market Data Service prices, Portfolio DB
Success Criteria:
  - Total Value = Σ(quantity × current_price)
  - Gain/Loss = Total Value - Total Cost
  - ROI% = (Gain/Loss / Total Cost) × 100
  - Response time < 200ms for up to 100 assets
Files: portfolio_service/calculations/performance.py
Tests: test_portfolio_performance.py
```

### Frontend Tasks
```
ID: FRONTEND-001
Title: Create Dashboard Page Layout
Description: Build React dashboard with layout structure
Dependencies: React 18, TailwindCSS, shadcn/ui
Success Criteria:
  - Header with navigation and user menu
  - Sidebar with page links
  - Main content area (responsive)
  - Footer
  - Mobile responsive (320px+)
Files: frontend/src/pages/dashboard.tsx
Tests: frontend/src/__tests__/dashboard.test.tsx

---

ID: FRONTEND-002
Title: Implement Real-Time Price Chart
Description: Build interactive price chart with WebSocket updates
Dependencies: Recharts, WebSocket API
Success Criteria:
  - Displays last 24h price history
  - Updates every 1-2 seconds via WebSocket
  - Time range selector (1H, 24H, 7D, 1M)
  - Zoom and pan functionality
  - Performance: < 500ms render time for 1000 points
Files: frontend/src/components/PriceChart.tsx
Tests: frontend/src/__tests__/PriceChart.test.tsx

---

ID: FRONTEND-003
Title: Implement Portfolio Dashboard
Description: Show portfolio value, asset allocation, performance
Dependencies: Redux state, Portfolio API
Success Criteria:
  - Total portfolio value display
  - Asset allocation pie chart
  - Assets table with quantity, price, gain/loss
  - Performance trend chart
  - Add/edit asset modal
Files: frontend/src/pages/portfolio.tsx
Tests: frontend/src/__tests__/portfolio.test.tsx
```

### DevOps Tasks
```
ID: DEVOPS-001
Title: Create Kubernetes Manifests
Description: Write K8s deployment files for all services
Dependencies: Kubernetes 1.24+
Success Criteria:
  - Deployments for each service with resource limits
  - Services for internal communication
  - ConfigMaps for environment variables
  - Secrets for sensitive data
  - PersistentVolumeClaims for databases
Files: k8s/*.yaml
Tests: kubectl apply --dry-run

---

ID: DEVOPS-002
Title: Setup Prometheus Monitoring
Description: Configure Prometheus scraping and alerting rules
Dependencies: Prometheus 2.40+
Success Criteria:
  - Scrapes metrics from all services every 15s
  - Stores 15-day retention
  - Alert rules for CPU > 80%, Memory > 90%, Error rate > 1%
  - Loki integration for logs
Files: monitoring/prometheus.yml, monitoring/alerts.yml
Tests: promtool check config
```

---

## 16. Code Quality Standards

### Python (FastAPI Services)
```
- Type hints: 100% coverage required
- Docstrings: Google style, on all functions
- Linting: pylint score > 9.0
- Tests: coverage > 80%
- Formatting: black (line length 100)
- Async/await: Use asyncio for I/O operations
```

### TypeScript/React (Frontend)
```
- Type safety: strict mode enabled
- Props: typed with interfaces
- State: Redux with typed reducers
- Tests: Jest + React Testing Library
- Coverage: > 80%
- Linting: ESLint with prettier
```

### SQL
```
- All queries parameterized (no string interpolation)
- Indexes on foreign keys and WHERE columns
- Comments on complex queries
- Migrations: One change per file
```

---

## 17. Testing Requirements

### Unit Tests
- **Location**: `tests/unit/` for each service
- **Coverage**: > 80% of code
- **Framework**: pytest (Python), Jest (TypeScript)
- **Command**: `pytest --cov` or `npm test`

### Integration Tests
- **Location**: `tests/integration/`
- **Scope**: Service-to-service communication, DB queries
- **Command**: `pytest tests/integration/`
- **Docker**: Run against docker-compose

### End-to-End Tests
- **Location**: `tests/e2e/`
- **Scope**: Full user workflows (register → create portfolio → track)
- **Command**: `npm run test:e2e` (frontend)
- **Tools**: Cypress or Playwright

### Load Tests
- **Tool**: Apache JMeter or k6
- **Targets**: 
  - 10,000 req/s on API Gateway
  - 50,000 concurrent WebSocket connections
- **Success**: p95 latency < targets in Performance section

---

## 18. Environment Variables

### All Services
```
DATABASE_URL=postgresql://user:pass@postgres:5432/crypto_db
REDIS_URL=redis://redis:6379/0
KAFKA_BROKERS=kafka-0:9092,kafka-1:9092,kafka-2:9092
LOG_LEVEL=INFO
ENVIRONMENT=development|staging|production
```

### Market Data Service
```
BINANCE_WS_URL=wss://stream.binance.com:9443/ws
COINBASE_API_KEY=xxx
COINBASE_API_SECRET=xxx
```

### Sentiment Service
```
NEWSAPI_KEY=xxx
HUGGINGFACE_MODEL=distilbert-base-uncased-finetuned-sst-2-english
```

### Frontend
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

---

## 19. Success Metrics

### Performance
- [ ] API Gateway: 99th percentile latency < 200ms
- [ ] Database queries: < 100ms (p95)
- [ ] WebSocket messages: < 50ms end-to-end
- [ ] Frontend page load: < 3 seconds

### Reliability
- [ ] System uptime: 99.5% or higher
- [ ] Error rate: < 0.5%
- [ ] Failed health checks: 0
- [ ] Data loss incidents: 0

### Code Quality
- [ ] Test coverage: > 80%
- [ ] Lint warnings: 0
- [ ] Security vulnerabilities: 0
- [ ] Code review approved: 100%

### User Experience
- [ ] Real-time price updates: < 2 seconds
- [ ] Portfolio calculation: < 300ms
- [ ] Mobile responsiveness: 100% on standard devices
- [ ] Accessibility score: > 90

---

**Document Status**: AI-Agent Ready  
**Last Updated**: October 25, 2025  
**Recommended Agent**: GPT-4, Claude 3.5+, Gemini 1.5+
