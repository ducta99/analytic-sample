#!/bin/bash

echo "================================================"
echo "🚀 Starting Cryptocurrency Analytics Backend"
echo "================================================"

cd /home/duc/analytics

# Set environment variables
export PYTHONPATH="/home/duc/analytics:$PYTHONPATH"
export DATABASE_URL="postgresql+asyncpg://crypto_user:crypto_password@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export JWT_SECRET="your-secret-key-change-in-production"
export JWT_ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="1440"

echo ""
echo "📋 Step 1: Checking Infrastructure..."
echo "----------------------------------------"

# Check Docker containers
if ! docker ps | grep -q crypto-postgres; then
    echo "❌ Docker containers not running!"
    echo "Starting infrastructure..."
    docker-compose up -d postgres redis kafka zookeeper
    echo "⏳ Waiting 10 seconds for services to start..."
    sleep 10
else
    echo "✅ Infrastructure already running"
fi

echo ""
echo "📋 Step 2: Starting API Gateway (Port 8000)..."
echo "----------------------------------------"

pkill -f "uvicorn.*8000" 2>/dev/null || true
cd /home/duc/analytics/api-gateway
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /home/duc/analytics/logs/api-gateway.log 2>&1 &
echo "✅ API Gateway starting... (PID: $!)"

echo ""
echo "📋 Step 3: Starting Microservices..."
echo "----------------------------------------"

# User Service
cd /home/duc/analytics/user-service
pkill -f "uvicorn.*8001" 2>/dev/null || true
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 > /home/duc/analytics/logs/user-service.log 2>&1 &
echo "✅ User Service starting... (PID: $!)"

# Market Data Service (without Kafka for now)
cd /home/duc/analytics/market-data-service
pkill -f "uvicorn.*8002" 2>/dev/null || true
nohup uvicorn app.main:app --host 0.0.0.0 --port 8002 > /home/duc/analytics/logs/market-data.log 2>&1 &
echo "⚠️  Market Data Service starting... (PID: $!) - May fail if Kafka unhealthy"

# Analytics Service
cd /home/duc/analytics/analytics-service
pkill -f "uvicorn.*8003" 2>/dev/null || true
nohup uvicorn app.main:app --host 0.0.0.0 --port 8003 > /home/duc/analytics/logs/analytics.log 2>&1 &
echo "✅ Analytics Service starting... (PID: $!)"

# Sentiment Service
cd /home/duc/analytics/sentiment-service
pkill -f "uvicorn.*8004" 2>/dev/null || true
nohup uvicorn app.main:app --host 0.0.0.0 --port 8004 > /home/duc/analytics/logs/sentiment.log 2>&1 &
echo "✅ Sentiment Service starting... (PID: $!)"

# Portfolio Service
cd /home/duc/analytics/portfolio-service
pkill -f "uvicorn.*8005" 2>/dev/null || true
nohup uvicorn app.main:app --host 0.0.0.0 --port 8005 > /home/duc/analytics/logs/portfolio.log 2>&1 &
echo "✅ Portfolio Service starting... (PID: $!)"

echo ""
echo "⏳ Waiting 8 seconds for services to initialize..."
sleep 8

echo ""
echo "📋 Step 4: Health Check..."
echo "----------------------------------------"

for port in 8000 8001 8002 8003 8004 8005; do
    # Market Data service has /api/market prefix
    if [ "$port" = "8002" ]; then
        response=$(curl -s -w "\n%{http_code}" http://localhost:$port/api/market/health 2>/dev/null || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" http://localhost:$port/health 2>/dev/null || echo "000")
    fi
    http_code=$(echo "$response" | tail -1)
    
    if [ "$http_code" = "200" ]; then
        echo "✅ Port $port: HEALTHY"
    else
        echo "❌ Port $port: NOT RESPONDING"
    fi
done

echo ""
echo "================================================"
echo "✨ Backend Services Started!"
echo "================================================"
echo ""
echo "📖 API Documentation:"
echo "   • API Gateway:    http://localhost:8000/docs"
echo "   • User Service:   http://localhost:8001/docs"
echo "   • Market Data:    http://localhost:8002/docs"
echo "   • Analytics:      http://localhost:8003/docs"
echo "   • Sentiment:      http://localhost:8004/docs"
echo "   • Portfolio:      http://localhost:8005/docs"
echo ""
echo "📝 View Logs:"
echo "   tail -f /home/duc/analytics/logs/*.log"
echo ""
echo "🛑 Stop All Services:"
echo "   ./STOP_BACKEND.sh"
echo ""
