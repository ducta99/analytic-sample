# 🪙 Cryptocurrency Analytics Dashboard

A microservice-based real-time cryptocurrency analytics platform with real-time price aggregation, advanced analytics, sentiment analysis, and portfolio tracking.

## 📋 Project Overview

This project implements a comprehensive cryptocurrency analytics platform consisting of:

- **Real-time Price Aggregation**: Streaming from Binance & Coinbase exchanges
- **Advanced Analytics**: Moving averages (SMA/EMA), volatility calculation, price correlations
- **Sentiment Analysis**: NLP-based sentiment analysis from news sources
- **Portfolio Tracking**: User portfolio management with performance analytics
- **Enterprise-grade Architecture**: Microservices, event-driven, distributed caching, and monitoring

## 🏗️ System Architecture

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

## 📂 Project Structure

```
.
├── api-gateway/              # FastAPI API Gateway with routing and auth
├── user-service/             # User authentication and profile management
├── market-data-service/      # Real-time price streaming from exchanges
├── analytics-service/        # Analytics computation (moving averages, volatility)
├── sentiment-service/        # NLP sentiment analysis from news sources
├── frontend/                 # React/Next.js dashboard UI
├── shared/                   # Shared utilities, models, and helpers
│   ├── models/              # Common data models
│   └── utils/               # Shared utility functions
├── k8s/                     # Kubernetes manifests for deployment
├── migrations/              # Database migration scripts
├── monitoring/              # Prometheus, Grafana configs
├── tests/                   # Integration and e2e tests
├── docs/                    # Documentation and diagrams
├── docker-compose.yml       # Local development setup
├── .gitignore              # Git ignore patterns
├── SPECIFICATION.md         # Full technical specification
└── TODO.md                  # Task list and progress tracking
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or use Docker)
- Redis 7+ (or use Docker)
- Kafka 3.5+ (or use Docker)

### Local Development with Docker Compose

```bash
# Clone the repository
git clone <repo-url>
cd analytics

# Start all services
docker-compose up --build

# The system will be available at:
# - Frontend: http://localhost:3000
# - API Gateway: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Manual Setup

```bash
# 1. Install Python dependencies for each service
cd api-gateway && pip install -r requirements.txt
cd ../user-service && pip install -r requirements.txt
# ... repeat for each service

# 2. Setup database
psql -U postgres -d crypto_db -f migrations/001_initial_schema.sql

# 3. Run services
# In separate terminals:
cd api-gateway && python -m app.main
cd user-service && python -m app.main
# ... etc
```

## 🔑 Key Features

### User Service
- User registration and authentication (JWT)
- Password hashing with bcrypt
- Email validation
- User profile management
- Preferences and settings

### Market Data Service
- Real-time WebSocket connections to Binance & Coinbase
- Automatic reconnection with exponential backoff
- Kafka producer for real-time price updates
- Data normalization across exchanges
- Health check endpoint

### Analytics Service
- Simple Moving Average (SMA) calculation
- Exponential Moving Average (EMA) calculation
- Volatility index (standard deviation)
- Price correlation analysis
- Batch processing for efficiency
- Redis caching with TTL

### Sentiment Service
- News article ingestion from NewsAPI
- NLP sentiment classification
- Positive/negative/neutral classification
- Trend analysis
- Social media sentiment integration (optional)

### Portfolio Service
- Portfolio creation and management
- Asset tracking with quantity and cost basis
- Performance calculation (total value, gain/loss, ROI%)
- Watchlist functionality
- Portfolio history tracking

## 📊 Data Models

### Key Tables
- **users**: User accounts and authentication
- **coins**: Cryptocurrency information (symbol, name, rank)
- **prices**: Time-series price data (coin_id, price, volume, timestamp)
- **portfolios**: User portfolios
- **portfolio_assets**: Assets within portfolios
- **sentiments**: Sentiment scores by coin and time

See `migrations/` for full schema definitions.

## 🔌 API Endpoints

### User Service
```
POST   /api/users/register              - Create new account
POST   /api/users/login                 - User login with JWT
GET    /api/users/{user_id}             - Get user profile
PUT    /api/users/{user_id}             - Update profile
GET    /api/users/{user_id}/preferences - Get user preferences
PUT    /api/users/{user_id}/preferences - Update preferences
```

### Market Data Service
```
GET    /api/market/price/{coin_id}      - Get current price
WS     /api/market/stream               - Real-time price stream
```

### Analytics Service
```
GET    /api/analytics/moving-average/{coin_id}  - SMA/EMA for coin
GET    /api/analytics/volatility/{coin_id}      - Volatility for coin
GET    /api/analytics/correlation                - Correlation between coins
```

### Sentiment Service
```
GET    /api/sentiment/{coin_id}         - Sentiment score for coin
GET    /api/sentiment/{coin_id}/trend   - Sentiment trend over time
GET    /api/sentiment/news/{coin_id}    - News articles for coin
```

### Portfolio Service
```
POST   /api/portfolio                   - Create portfolio
GET    /api/portfolio                   - List user portfolios
GET    /api/portfolio/{portfolio_id}    - Get portfolio details
PUT    /api/portfolio/{portfolio_id}    - Update portfolio
DELETE /api/portfolio/{portfolio_id}    - Delete portfolio
POST   /api/portfolio/{portfolio_id}/assets - Add asset
GET    /api/portfolio/{portfolio_id}/performance - Performance metrics
```

## 🔐 Security Features

- JWT authentication with 7-day refresh tokens
- bcrypt password hashing (12+ rounds)
- SQL injection prevention (parameterized queries)
- CORS configuration with allowed origins
- Rate limiting per user and endpoint
- HTTPS/TLS support
- WSS (Secure WebSocket) support
- CSRF protection for state-changing operations
- Environment-based secret management

## 📈 Performance Targets

| Metric | Target |
|--------|--------|
| GET /prices latency | < 100ms (p95) |
| GET /analytics latency | < 200ms (p95) |
| GET /portfolio latency | < 200ms (p95) |
| API throughput | 10,000 req/s |
| WebSocket connections | 50,000 concurrent |
| Initial page load | < 3s |
| Chart rendering (1000 points) | < 500ms |
| Uptime SLA | 99.5% |

## 🧪 Testing

```bash
# Run all tests
pytest tests/ --cov

# Run specific service tests
cd user-service && pytest tests/ --cov

# Run with coverage report
pytest tests/ --cov --cov-report=html
```

**Coverage Target**: > 80% code coverage

## 📊 Monitoring & Logging

- **Prometheus**: Metrics collection (15s scrape interval, 15-day retention)
- **Grafana**: Dashboards and visualization
- **Loki**: Log aggregation (30-day retention)
- **Alert Rules**: CPU > 80%, Memory > 90%, Error rate > 1%

Access Grafana at: http://localhost:3001 (default creds: admin/admin)

## 🚢 Deployment

### Docker Compose (Development)
```bash
docker-compose up --build
```

### Kubernetes (Production)
```bash
kubectl create namespace crypto
kubectl apply -f k8s/
```

See `docs/deployment-guide.md` for detailed instructions.

## 📖 Documentation

- `SPECIFICATION.md` - Full technical specification
- `docs/API.md` - API documentation
- `docs/architecture.md` - System architecture details
- `docs/deployment-guide.md` - Deployment instructions
- `docs/developer-guide.md` - Development guide

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL 14+
- **Cache**: Redis 7+
- **Message Queue**: Kafka 3.5+
- **Language**: Python 3.11+

### Frontend
- **Framework**: React 18 / Next.js 14
- **Styling**: TailwindCSS
- **Components**: shadcn/ui
- **Charts**: Recharts
- **State**: Redux Toolkit
- **Language**: TypeScript

### DevOps
- **Containers**: Docker & Docker Compose
- **Orchestration**: Kubernetes 1.24+
- **Monitoring**: Prometheus, Grafana, Loki
- **CI/CD**: GitHub Actions

## 📝 Development Workflow

1. **Create a feature branch**: `git checkout -b feature/your-feature`
2. **Make changes** and write tests
3. **Run tests locally**: `pytest tests/ --cov`
4. **Commit changes**: `git commit -m "feat: your feature"`
5. **Push to remote**: `git push origin feature/your-feature`
6. **Create pull request** for code review

## 🤝 Contributing

Contributions are welcome! Please:
1. Follow the code style (Black for Python, Prettier for TypeScript)
2. Add tests for new features
3. Maintain > 80% code coverage
4. Update documentation as needed
5. Follow commit message conventions

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation in `docs/`
- Review `SPECIFICATION.md` for detailed requirements

---

**Last Updated**: October 25, 2025  
**Version**: 1.0 (In Development)  
**Status**: Phase 1 - Foundation & Setup
