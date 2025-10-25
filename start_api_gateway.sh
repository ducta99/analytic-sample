#!/bin/bash
# Start API Gateway with proper Python path

cd /home/duc/analytics

# Set environment variables
export DATABASE_URL="postgresql://crypto_user:crypto_password@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379/0"
export KAFKA_BROKERS="localhost:9092"
export JWT_SECRET_KEY="your-secret-key-change-in-production"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRATION_HOURS="24"
export LOG_LEVEL="INFO"
export ENVIRONMENT="development"

# Add project root to Python path
export PYTHONPATH="/home/duc/analytics:$PYTHONPATH"

echo "🚀 Starting API Gateway on port 8000..."
echo "📖 API Docs will be available at: http://localhost:8000/docs"
echo ""

cd api-gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
