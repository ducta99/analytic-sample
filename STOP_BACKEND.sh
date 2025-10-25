#!/bin/bash

echo "================================================"
echo "🛑 Stopping All Backend Services"
echo "================================================"

cd /home/duc/analytics

echo ""
echo "Stopping microservices..."

# Stop all uvicorn processes
pkill -f "uvicorn.*8000" && echo "✅ Stopped API Gateway (8000)"
pkill -f "uvicorn.*8001" && echo "✅ Stopped User Service (8001)"
pkill -f "uvicorn.*8002" && echo "✅ Stopped Market Data (8002)"
pkill -f "uvicorn.*8003" && echo "✅ Stopped Analytics (8003)"
pkill -f "uvicorn.*8004" && echo "✅ Stopped Sentiment (8004)"
pkill -f "uvicorn.*8005" && echo "✅ Stopped Portfolio (8005)"

echo ""
echo "✨ All backend services stopped"
echo ""
