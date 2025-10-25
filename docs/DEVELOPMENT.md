# Developer Guide

**Version**: 1.0  
**Last Updated**: October 25, 2025

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Getting Started](#getting-started)
4. [Development Workflow](#development-workflow)
5. [Architecture](#architecture)
6. [Adding Features](#adding-features)
7. [Testing](#testing)
8. [Code Standards](#code-standards)
9. [Debugging](#debugging)
10. [Performance Tips](#performance-tips)

---

## Project Overview

**Cryptocurrency Analytics Dashboard** is a microservices-based platform for real-time cryptocurrency analysis, portfolio tracking, and market sentiment analysis.

**Key Technologies**:
- **Backend**: Python (FastAPI), PostgreSQL, Redis, Kafka
- **Frontend**: React 18/Next.js 14, TypeScript, TailwindCSS
- **DevOps**: Docker, Kubernetes, GitHub Actions
- **Monitoring**: Prometheus, Grafana, Loki

---

## Project Structure

```
analytics/
├── api-gateway/                 # Central API routing & authentication
│   ├── app/
│   │   ├── main.py             # FastAPI application
│   │   ├── schemas.py          # Request/response schemas
│   │   └── middleware/
│   │       ├── auth.py         # JWT validation
│   │       ├── error_handler.py # Exception handling
│   │       └── prometheus.py    # Metrics collection
│   ├── tests/                  # Unit tests
│   └── Dockerfile
│
├── user_service/                # Authentication & user management
│   ├── app/
│   │   ├── main.py
│   │   ├── models/             # Database models
│   │   ├── routes/             # API endpoints
│   │   └── schemas.py
│   └── tests/
│
├── market_data_service/         # Real-time price streaming
│   ├── app/
│   │   ├── main.py
│   │   ├── clients/            # Exchange API clients
│   │   ├── routes.py
│   │   └── schemas.py
│   └── tests/
│
├── analytics_service/           # Technical analysis & metrics
│   ├── app/
│   │   ├── main.py
│   │   ├── calculations/       # SMA, EMA, volatility
│   │   └── routes.py
│   └── tests/
│
├── sentiment_service/           # NLP sentiment analysis
│   ├── app/
│   │   ├── main.py
│   │   ├── nlp/                # ML models
│   │   ├── ingestors/          # Data sources
│   │   └── routes.py
│   └── tests/
│
├── portfolio_service/           # Portfolio management
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── calculations/       # Performance metrics
│   │   └── routes.py
│   └── tests/
│
├── frontend/                    # React/Next.js dashboard
│   ├── src/
│   │   ├── app/                # Next.js pages
│   │   │   ├── page.tsx        # Dashboard
│   │   │   ├── portfolio/
│   │   │   ├── analytics/
│   │   │   ├── sentiment/
│   │   │   └── auth/
│   │   ├── components/         # Reusable components
│   │   ├── types/              # TypeScript types
│   │   └── utils/              # Utilities & API client
│   ├── package.json
│   └── Dockerfile
│
├── shared/                      # Shared utilities
│   ├── config/                 # Configuration
│   ├── models/                 # Shared data models
│   ├── utils/
│   │   ├── auth.py             # JWT utilities
│   │   ├── logging_config.py
│   │   ├── metrics.py          # Prometheus metrics
│   │   └── exceptions.py
│   └── requirements-base.txt
│
├── k8s/                         # Kubernetes manifests
│   ├── 01-infrastructure.yaml
│   ├── 02-services.yaml
│   └── ...
│
├── monitoring/                  # Monitoring configs
│   ├── prometheus.yml
│   ├── grafana.yml
│   └── dashboards/
│
├── migrations/                  # Database migrations
│   └── 001_initial_schema.sql
│
├── tests/                       # Integration & E2E tests
│   ├── e2e_tests.py
│   └── load_tests.js
│
├── docs/                        # Documentation
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── DEVELOPMENT.md
│   └── architecture.md
│
├── docker-compose.yml           # Local development
└── README.md
```

---

## Getting Started

### Prerequisites

```bash
# Python 3.11+
python --version

# Node.js 18+
node --version

# Docker & Docker Compose
docker --version
docker-compose --version

# PostgreSQL client (optional)
psql --version
```

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd analytics

# Create virtual environment (Python)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r shared/requirements-base.txt
pip install -r api-gateway/requirements.txt

# Install Node dependencies
cd frontend
npm install

# Setup environment
cp .env.example .env

# Start services
docker-compose up -d
```

### Verify Installation

```bash
# Check API Gateway
curl http://localhost:8000/health

# Check Frontend
curl http://localhost:3000

# Check Database
psql -U crypto_user -d crypto_db -c "SELECT version();"
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/add-new-analytics
```

### 2. Make Changes

```bash
# Backend changes
vi analytics_service/app/routes.py

# Frontend changes
vi frontend/src/components/NewComponent.tsx
```

### 3. Test Changes

```bash
# Run unit tests
pytest tests/ -v

# Run linting
black . --check
pylint app/

# Type checking
mypy . --ignore-missing-imports

# Frontend tests
cd frontend
npm test
npm run lint
```

### 4. Commit & Push

```bash
git add .
git commit -m "feat: add new analytics endpoint"
git push origin feature/add-new-analytics
```

### 5. Create Pull Request

- Create PR on GitHub
- Add description of changes
- Reference any related issues
- Wait for CI/CD to pass
- Request review from team members

### 6. Merge & Deploy

- Squash commits if needed
- Merge to main/develop
- CI/CD pipeline runs automatically
- Services deployed to production

---

## Architecture

### Service Communication

```
Frontend (React/Next.js)
        ↓ HTTP/WebSocket
    API Gateway (FastAPI)
        ↓
┌───────────────────────────────────────┐
│ User   │ Market  │ Analytics │ Sentiment │
│Service │ Data    │ Service   │ Service   │
└───────────────────────────────────────┘
        ↓ Async (Kafka)
┌───────────────────────────────────────┐
│ Redis Cache │ PostgreSQL │ Kafka Queue │
└───────────────────────────────────────┘
```

### Request Flow

1. Frontend sends request to API Gateway
2. API Gateway validates JWT token
3. Request routed to appropriate microservice
4. Service queries database/cache
5. Service publishes event to Kafka (if applicable)
6. Response returned to Frontend
7. Analytics/Sentiment services consume Kafka events

---

## Adding Features

### Add New API Endpoint

1. **Create schema** (`app/schemas.py`):

```python
from pydantic import BaseModel, Field

class NewRequest(BaseModel):
    param1: str = Field(..., description="Parameter 1")
    param2: int = Field(default=10)

class NewResponse(BaseModel):
    result: str
    timestamp: datetime
```

2. **Create route** (`app/routes.py`):

```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/new-endpoint", response_model=NewResponse)
async def new_endpoint(request: NewRequest):
    """Description of endpoint."""
    return NewResponse(result="success")
```

3. **Add to main app** (`app/main.py`):

```python
from app.routes import router
app.include_router(router, prefix="/api", tags=["new"])
```

4. **Write tests** (`tests/test_new_endpoint.py`):

```python
def test_new_endpoint():
    response = client.post("/api/new-endpoint", json={
        "param1": "test",
        "param2": 5
    })
    assert response.status_code == 200
    assert response.json()["result"] == "success"
```

### Add New Frontend Component

1. **Create component** (`src/components/NewComponent.tsx`):

```typescript
import React from 'react';

interface NewComponentProps {
  title: string;
  onAction?: () => void;
}

const NewComponent: React.FC<NewComponentProps> = ({ title, onAction }) => {
  return (
    <div className="p-4 bg-gray-800 rounded-lg">
      <h2 className="text-xl font-bold">{title}</h2>
      <button onClick={onAction} className="mt-2 px-4 py-2 bg-blue-600 rounded">
        Action
      </button>
    </div>
  );
};

export default NewComponent;
```

2. **Add to page** (`src/app/page.tsx`):

```typescript
import NewComponent from '@/components/NewComponent';

export default function Home() {
  return (
    <main>
      <NewComponent title="My Component" />
    </main>
  );
}
```

3. **Add tests** (`src/__tests__/NewComponent.test.tsx`):

```typescript
import { render, screen } from '@testing-library/react';
import NewComponent from '@/components/NewComponent';

test('renders with title', () => {
  render(<NewComponent title="Test" />);
  expect(screen.getByText('Test')).toBeInTheDocument();
});
```

---

## Testing

### Run All Tests

```bash
# Python
pytest tests/ -v --cov

# TypeScript/React
cd frontend
npm test

# E2E tests
pytest tests/e2e_tests.py -v

# Load tests (k6)
k6 run tests/load_tests.js
```

### Test Coverage

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html

# View report
open htmlcov/index.html

# Frontend coverage
cd frontend
npm test -- --coverage
```

### Run Specific Test

```bash
# Single file
pytest tests/test_auth.py -v

# Single test
pytest tests/test_auth.py::test_login -v

# Matching pattern
pytest -k "test_portfolio" -v
```

---

## Code Standards

### Python

- **Formatter**: Black (line length: 100)
- **Linter**: pylint
- **Type Checking**: mypy
- **Docstrings**: Google style

```python
def calculate_average(prices: List[float]) -> float:
    """Calculate average price from price list.
    
    Args:
        prices: List of price values
        
    Returns:
        Average price
        
    Raises:
        ValueError: If prices list is empty
    """
    if not prices:
        raise ValueError("Prices list cannot be empty")
    return sum(prices) / len(prices)
```

### TypeScript/React

- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Safety**: strict mode enabled
- **Props**: Always typed with interfaces

```typescript
interface ButtonProps {
  onClick: () => void;
  label: string;
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ onClick, label, disabled }) => (
  <button onClick={onClick} disabled={disabled}>
    {label}
  </button>
);
```

### SQL

- Parameterized queries only (no string interpolation)
- Meaningful comments for complex queries
- Indexes on foreign keys

```sql
-- Get portfolio with performance metrics
SELECT 
  p.id,
  p.name,
  SUM(pa.quantity * pr.price) as current_value,
  SUM(pa.quantity * pa.purchase_price) as total_cost
FROM portfolios p
JOIN portfolio_assets pa ON p.id = pa.portfolio_id
JOIN prices pr ON pa.coin_id = pr.coin_id
WHERE p.user_id = $1
GROUP BY p.id;
```

---

## Debugging

### Server-Side Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use modern Python 3.7+
breakpoint()

# Debug with logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {variable}")
```

### Frontend Debugging

```typescript
// Browser console
console.log('Debug message:', value);

// Debugger statement
debugger;

// React DevTools Chrome extension

// Network tab to inspect API calls
```

### Docker Debugging

```bash
# Enter running container
docker exec -it container_name bash

# Check service logs
docker logs -f service_name

# Inspect network
docker network ls
docker network inspect network_name
```

### Kubernetes Debugging

```bash
# Exec into pod
kubectl exec -it pod_name -n namespace -- bash

# Port forward for local debugging
kubectl port-forward pod_name 8000:8000 -n namespace

# Stream logs
kubectl logs -f pod_name -n namespace
```

---

## Performance Tips

### Backend Optimization

```python
# Use batch operations
# ❌ Bad: N+1 queries
for portfolio in portfolios:
    print(portfolio.assets)  # Triggers query per portfolio

# ✅ Good: Eager loading
portfolios = Portfolio.query.options(joinedload(Portfolio.assets))

# Cache expensive operations
@cache(ttl=300)
def get_market_summary():
    # Expensive calculation
    return summary

# Use pagination
@app.get("/items")
async def list_items(skip: int = 0, limit: int = 10):
    return db.query(Item).offset(skip).limit(limit)
```

### Frontend Optimization

```typescript
// Code splitting
const PortfolioPage = lazy(() => import('./Portfolio'));

// Memoization
const ExpensiveComponent = memo(({ data }) => {
  return <div>{data.map(item => ...)}</div>;
});

// Image optimization
<Image src={url} alt={alt} width={100} height={100} />

// Bundle analysis
npm run build -- --analyze
```

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_portfolio_user ON portfolio_assets(user_id);
CREATE INDEX idx_prices_coin_timestamp ON prices(coin_id, timestamp DESC);

-- Use EXPLAIN to analyze queries
EXPLAIN ANALYZE SELECT * FROM portfolios WHERE user_id = 1;

-- Monitor slow queries
SET log_min_duration_statement = 1000;  -- Log queries > 1s
```

### Monitoring & Profiling

```bash
# Python profiling
python -m cProfile -s cumtime app/main.py

# Memory profiling
pip install memory_profiler
python -m memory_profiler app/main.py

# Load testing
k6 run tests/load_tests.js

# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds
```

---

## Resources

- **API Documentation**: `docs/API.md`
- **Architecture**: `docs/architecture.md`
- **Deployment**: `docs/DEPLOYMENT.md`
- **Specification**: `SPECIFICATION.md`

---

**Questions?** Check existing issues or create a new one.

**Ready to contribute?** See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Last Updated**: October 25, 2025  
**Version**: 1.0.0
