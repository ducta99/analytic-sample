#!/bin/bash

# Start all microservices for the Cryptocurrency Analytics Platform
# Each service runs in the background with logs redirected to service-specific files

set -e

PROJECT_ROOT="/home/duc/analytics"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Environment variables
export DATABASE_URL="postgresql+asyncpg://crypto_user:crypto_pass@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export JWT_SECRET="your-secret-key-change-in-production"
export JWT_ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="1440"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Cryptocurrency Analytics Platform Services...${NC}\n"

# Function to start a service
start_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    
    echo -e "${YELLOW}Starting $service_name on port $port...${NC}"
    
    cd "$PROJECT_ROOT/$service_dir"
    nohup uvicorn app.main:app --host 0.0.0.0 --port $port > "$PROJECT_ROOT/logs/${service_name}.log" 2>&1 &
    
    echo $! > "$PROJECT_ROOT/logs/${service_name}.pid"
    
    echo -e "${GREEN}✓ $service_name started (PID: $(cat $PROJECT_ROOT/logs/${service_name}.pid))${NC}"
}

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Start services in dependency order
echo -e "\n${BLUE}Step 1: Starting User Service (Authentication)...${NC}"
start_service "user-service" "user-service" 8001

echo -e "\n${BLUE}Step 2: Starting Market Data Service...${NC}"
start_service "market-data-service" "market-data-service" 8002

echo -e "\n${BLUE}Step 3: Starting Analytics Service...${NC}"
start_service "analytics-service" "analytics-service" 8003

echo -e "\n${BLUE}Step 4: Starting Sentiment Service...${NC}"
start_service "sentiment-service" "sentiment-service" 8004

echo -e "\n${BLUE}Step 5: Starting Portfolio Service...${NC}"
start_service "portfolio-service" "portfolio-service" 8005

# Wait a bit for services to start
echo -e "\n${YELLOW}⏳ Waiting 5 seconds for services to initialize...${NC}"
sleep 5

# Check service health
echo -e "\n${BLUE}🏥 Health Check Status:${NC}\n"

check_health() {
    local service_name=$1
    local port=$2
    
    response=$(curl -s -w "\n%{http_code}" http://localhost:$port/health 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ $service_name (port $port): HEALTHY${NC}"
    else
        echo -e "${YELLOW}⚠ $service_name (port $port): NOT RESPONDING (may still be starting)${NC}"
    fi
}

check_health "API Gateway" 8000
check_health "User Service" 8001
check_health "Market Data Service" 8002
check_health "Analytics Service" 8003
check_health "Sentiment Service" 8004
check_health "Portfolio Service" 8005

echo -e "\n${BLUE}📊 Service URLs:${NC}"
echo -e "  • API Gateway:        http://localhost:8000/docs"
echo -e "  • User Service:       http://localhost:8001/docs"
echo -e "  • Market Data:        http://localhost:8002/docs"
echo -e "  • Analytics:          http://localhost:8003/docs"
echo -e "  • Sentiment:          http://localhost:8004/docs"
echo -e "  • Portfolio:          http://localhost:8005/docs"

echo -e "\n${BLUE}📝 Logs are available in: $PROJECT_ROOT/logs/${NC}"
echo -e "\n${GREEN}✨ All services started successfully!${NC}"
echo -e "\n${YELLOW}To stop all services, run: ./stop_all_services.sh${NC}\n"
