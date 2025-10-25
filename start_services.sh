#!/bin/bash
# ============================================================================
# Start Backend Services - Without Docker
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════"
echo "  🚀 Starting Cryptocurrency Analytics Platform Services"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Export environment variables
export DATABASE_URL="postgresql://crypto_user:crypto_password@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379/0"
export KAFKA_BROKERS="localhost:9092"
export JWT_SECRET_KEY="your-secret-key-change-in-production"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRATION_HOURS="24"
export LOG_LEVEL="INFO"
export ENVIRONMENT="development"

echo -e "${BLUE}Infrastructure Status:${NC}"
echo "  PostgreSQL: localhost:5432"
echo "  Redis: localhost:6379"
echo "  Kafka: localhost:9092"
echo ""

echo -e "${YELLOW}Note: Run each service in a separate terminal:${NC}"
echo ""

echo -e "${GREEN}1. API Gateway (Port 8000):${NC}"
echo "   cd api-gateway && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""

echo -e "${GREEN}2. User Service (Port 8001):${NC}"
echo "   cd user-service && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"
echo ""

echo -e "${GREEN}3. Market Data Service (Port 8002):${NC}"
echo "   cd market-data-service && uvicorn app.main:app --reload --host 0.0.0.0 --port 8002"
echo ""

echo -e "${GREEN}4. Analytics Service (Port 8003):${NC}"
echo "   cd analytics-service && uvicorn app.main:app --reload --host 0.0.0.0 --port 8003"
echo ""

echo -e "${GREEN}5. Sentiment Service (Port 8004):${NC}"
echo "   cd sentiment-service && uvicorn app.main:app --reload --host 0.0.0.0 --port 8004"
echo ""

echo -e "${GREEN}6. Portfolio Service (Port 8005):${NC}"
echo "   cd portfolio-service && uvicorn app.main:app --reload --host 0.0.0.0 --port 8005"
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo -e "${BLUE}Quick Test:${NC}"
echo "  # Test API Gateway"
echo "  curl http://localhost:8000/health"
echo ""
echo "  # View API Documentation"
echo "  Open: http://localhost:8000/docs"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
