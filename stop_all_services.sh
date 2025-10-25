#!/bin/bash

# Stop all microservices

PROJECT_ROOT="/home/duc/analytics"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stopping Cryptocurrency Analytics Platform Services...${NC}\n"

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PROJECT_ROOT/logs/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${BLUE}Stopping $service_name (PID: $pid)...${NC}"
            kill $pid
            rm "$pid_file"
            echo -e "${GREEN}✓ $service_name stopped${NC}"
        else
            echo -e "${RED}⚠ $service_name process not found${NC}"
            rm "$pid_file"
        fi
    else
        echo -e "${RED}⚠ No PID file for $service_name${NC}"
    fi
}

# Stop all services
stop_service "user-service"
stop_service "market-data-service"
stop_service "analytics-service"
stop_service "sentiment-service"
stop_service "portfolio-service"

# Also stop API Gateway if it was started separately
echo -e "\n${BLUE}Stopping API Gateway...${NC}"
pkill -f "uvicorn.*8000" || echo -e "${RED}⚠ API Gateway not found${NC}"

echo -e "\n${GREEN}✨ All services stopped${NC}\n"
