# Copilot Instructions for Cryptocurrency Analytics Platform

## Architecture Overview

This is a **microservices-based real-time cryptocurrency analytics platform** with:
- **6 Python FastAPI services** (api-gateway, user-service, market-data-service, analytics-service, sentiment-service, portfolio-service)
- **Next.js 14 frontend** with TypeScript, TailwindCSS, and Redux Toolkit
- **Event-driven architecture** using Kafka for async communication between services
- **Distributed caching** with Redis (TTLs: 5s for prices, 1-5min for analytics, 5-10min for portfolios)
- **PostgreSQL** for persistent storage with connection pooling via `shared/db_pool.py`

## Critical Patterns & Conventions

### 1. Shared Utilities Pattern
All services depend on the `shared/` directory which contains:
- `shared/utils/auth.py` - JWT token creation/validation (HS256 algorithm, bcrypt password hashing)
- `shared/utils/exceptions.py` - Standardized exception hierarchy with HTTP status codes
- `shared/config/` - Cache TTL configs and key patterns (see `CacheConfig` class)
- `shared/db_pool.py` - AsyncIO database connection pooling with query performance tracking
- `shared/models/` - Common SQLAlchemy models

**When adding features:** Import from `shared/` rather than duplicating code. All exceptions MUST use the standardized `CryptoAnalyticsException` hierarchy.

### 2. Service Communication
- **Synchronous:** Frontend → API Gateway → Microservice (HTTP/REST)
- **Asynchronous:** Services publish to Kafka topics (`price_updates`, `sentiment_updates`)
  - Market Data Service: **Producer** on `price_updates`
  - Analytics Service: **Consumer** on `price_updates` (Kafka consumer initialized in lifespan)
  - Pattern: WebSocket data → Kafka → Batch processing → Redis cache

### 3. API Gateway Pattern
API Gateway (`api-gateway/app/main.py`) acts as the **single entry point**:
- Proxies requests to downstream services using `call_downstream_service()` helper
- JWT validation via `verify_token()` from `shared/utils/auth.py`
- Rate limiting with `slowapi` (5 req/min for auth endpoints)
- Request ID tracking via `RequestIDMiddleware` for distributed tracing
- Prometheus metrics collection via `PrometheusMiddleware`

**Service URLs are hardcoded:** `SERVICES` dict maps to internal Docker network addresses (e.g., `http://user-service:8001`)

### 4. Testing Architecture
- **Unit tests:** Each service has `tests/` with pytest using `pytest-asyncio`
- **Fixtures pattern:** See `portfolio-service/tests/conftest.py` for reusable fixtures
  - Uses in-memory SQLite (`sqlite+aiosqlite:///:memory:`) for fast tests
  - Fixtures for `db_session`, `sample_portfolio`, `sample_asset`, etc.
- **E2E tests:** `tests/e2e_tests.py` tests full workflows (register → login → create portfolio)
- **Load tests:** `tests/load_tests.js` uses k6 for performance testing

**Testing commands:**
```bash
pytest tests/ -v --cov              # Run with coverage
pytest tests/test_*.py::test_name   # Run specific test
```

### 5. Database Patterns
- **Async SQLAlchemy** with connection pooling (20 connections, 10 max_overflow)
- **Eager loading:** Use `joinedload()` and `selectinload()` to avoid N+1 queries (see `db_pool.py::optimize_portfolio_query()`)
- **Batch operations:** Use `batch_insert_prices()` and `batch_update_portfolios()` helpers for bulk operations
- **Query tracking:** Slow queries (>100ms) are automatically logged via SQLAlchemy event listeners
- **Migrations:** SQL files in `migrations/` (e.g., `001_initial_schema.sql`)

### 6. Cache Strategy
Redis keys follow strict patterns defined in `shared/config/__init__.py`:
```python
"price:{coin_id}"                                    # TTL: 10s
"analytics:moving_average:{coin_id}:{period}"       # TTL: 60s
"portfolio:{user_id}:{portfolio_id}"                # TTL: 600s
```
**Always use these patterns** - don't create ad-hoc cache keys.

### 7. Error Handling
All API responses follow this structure:
```json
{
  "success": true,
  "data": {...},
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```
Use exception hierarchy from `shared/utils/exceptions.py` - don't raise generic `Exception` or `HTTPException`.

### 8. Docker & Deployment
- **Multi-stage builds:** All Dockerfiles use builder pattern (see `user-service/Dockerfile`)
- **Docker Compose:** Local dev uses `docker-compose.yml` with health checks and dependency ordering
- **Kubernetes:** Production manifests in `k8s/` with resource limits and HPA configs
- **Health checks:** Every service exposes `/health` endpoint

### 9. Frontend Architecture
- **App Router:** Next.js 14 with file-based routing in `frontend/src/app/`
- **State:** Redux Toolkit for global state, local state for UI-only
- **API Client:** Axios with interceptors in `frontend/src/utils/api-client.ts`
- **WebSocket:** Custom `useWebSocket` hook for real-time price updates
- **Styling:** TailwindCSS with utility classes, avoid inline styles

## Development Workflow

### Adding a New Endpoint
1. Define Pydantic schemas in `app/schemas.py`
2. Create route in `app/routes.py` with OpenAPI docs
3. Add route to API Gateway's proxy layer
4. Write tests in `tests/test_*.py`
5. Update `docs/API.md` if public-facing

### Running Services Locally
```bash
docker-compose up -d          # Start all infrastructure
cd <service> && uvicorn app.main:app --reload --port 800X
cd frontend && npm run dev    # Frontend on :3000
```

### Common Commands
```bash
# Backend linting/formatting
black . --check && pylint app/

# Frontend
npm run lint && npm run type-check

# Database migrations
psql -U crypto_user -d crypto_db -f migrations/XXX.sql

# View logs
docker logs -f crypto-api-gateway

# Check Prometheus metrics
curl http://localhost:8000/metrics
```

## Service-Specific Notes

**Market Data Service:**
- Maintains persistent WebSocket connections to Binance/Coinbase
- Exponential backoff reconnection logic in `app/clients.py`
- Publishes normalized price events to Kafka every 1-2 seconds

**Analytics Service:**
- Kafka consumer runs in background via `asyncio.create_task()` in lifespan
- Calculations in `app/calculations.py`: SMA (simple average), EMA (K=2/(N+1)), Volatility (stddev)
- Results cached with 1-5 minute TTL

**Portfolio Service:**
- Performance calculations use current prices from Redis
- Batch updates for multiple assets via `batch_update_portfolios()`
- Historical snapshots stored in `portfolio_history` table

**API Gateway:**
- **Critical:** All downstream service calls go through `utils/service_client.py::call_downstream_service()`
- Rate limiting applied with `@limiter.limit("5/minute")` decorator
- Middleware stack order matters: RequestID → Prometheus → CORS → Error handling

## Monitoring & Observability

- **Prometheus:** Scrapes `/metrics` endpoint on each service (15s interval)
- **Grafana:** Dashboards in `monitoring/dashboards/` (API, Infrastructure, Business metrics)
- **Loki:** Structured JSON logs with `request_id` for tracing
- **Request tracing:** `X-Request-ID` header propagated across services

## Key Files to Reference

- `shared/config/__init__.py` - Cache TTLs and key patterns
- `shared/db_pool.py` - Database connection pooling and optimization patterns
- `shared/utils/exceptions.py` - All error codes and exception types
- `api-gateway/app/main.py` - Request routing and middleware setup
- `docs/architecture.md` - System design and data flows
- `docker-compose.yml` - Service dependencies and environment variables

## Anti-Patterns to Avoid

❌ Don't create custom exception types outside `shared/utils/exceptions.py`  
❌ Don't bypass API Gateway for inter-service calls  
❌ Don't use synchronous database calls (always use AsyncSession)  
❌ Don't hardcode cache TTLs (use `CacheConfig` constants)  
❌ Don't skip request ID propagation in new middleware  
❌ Don't use raw SQL without parameterization  
❌ Don't store secrets in code (use environment variables)
