# 🐳 Docker Infrastructure - Running Guide

## ✅ Current Status

### Infrastructure Services Running:
- ✅ **PostgreSQL** - localhost:5432 (healthy)
- ✅ **Redis** - localhost:6379 (healthy)  
- ✅ **Kafka** - localhost:9092 (healthy)
- ✅ **Zookeeper** - localhost:2181 (running)

### Database:
- ✅ **Schema initialized** - 11 tables created
- ✅ **Seed data loaded** - 10 cryptocurrencies

---

## 🚀 Next Steps

### Option 1: Run Services with Python (Recommended for Testing)

Each service needs to run in a **separate terminal**:

#### Terminal 1: API Gateway (Port 8000)
```bash
cd /home/duc/analytics
export DATABASE_URL="postgresql://crypto_user:crypto_password@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="your-secret-key-change-in-production"
export JWT_ALGORITHM="HS256"

cd api-gateway
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: User Service (Port 8001)
```bash
cd /home/duc/analytics
export DATABASE_URL="postgresql://crypto_user:crypto_password@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="your-secret-key-change-in-production"

cd user-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

#### Terminal 3: Market Data Service (Port 8002)
```bash
cd /home/duc/analytics
export REDIS_URL="redis://localhost:6379/0"
export KAFKA_BROKERS="localhost:9092"

cd market-data-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

#### Terminal 4: Analytics Service (Port 8003)
```bash
cd /home/duc/analytics
export DATABASE_URL="postgresql://crypto_user:crypto_password@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379/0"
export KAFKA_BROKERS="localhost:9092"

cd analytics-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

#### Terminal 5: Sentiment Service (Port 8004)
```bash
cd /home/duc/analytics
export DATABASE_URL="postgresql://crypto_user:crypto_password@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379/0"

cd sentiment-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

#### Terminal 6: Portfolio Service (Port 8005)
```bash
cd /home/duc/analytics
export DATABASE_URL="postgresql://crypto_user:crypto_password@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379/0"

cd portfolio-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

---

### Option 2: Use Helper Script

```bash
./start_services.sh
```

This will show you all the commands to copy/paste into separate terminals.

---

## 🧪 Testing the Services

### 1. Check Infrastructure
```bash
# Check Docker containers
docker-compose ps

# Test PostgreSQL
docker exec -it crypto-postgres psql -U crypto_user -d crypto_db -c "SELECT * FROM coins LIMIT 5;"

# Test Redis
docker exec -it crypto-redis redis-cli PING

# Test Kafka
docker exec -it crypto-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### 2. Test Services (Once Running)

```bash
# API Gateway health
curl http://localhost:8000/health

# User service health  
curl http://localhost:8001/health

# Market data health
curl http://localhost:8002/health

# Analytics health
curl http://localhost:8003/health

# Sentiment health
curl http://localhost:8004/health

# Portfolio health
curl http://localhost:8005/health
```

### 3. Test Complete Workflow

```bash
# Register a user
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Login
curl -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Get analytics (replace {token} with JWT from login)
curl http://localhost:8000/api/analytics/moving-average/bitcoin?period=20 \
  -H "Authorization: Bearer {token}"
```

---

## 📖 API Documentation

Once API Gateway is running:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## 🛑 Stopping Services

### Stop Python Services
Press `Ctrl+C` in each terminal

### Stop Docker Infrastructure
```bash
docker-compose down
```

### Stop and Remove Volumes (Clean Slate)
```bash
docker-compose down -v
```

---

## 🔧 Troubleshooting

### Issue: Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Issue: Database Connection Failed
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Issue: Redis Connection Failed
```bash
# Check Redis
docker-compose ps redis

# Test connection
docker exec -it crypto-redis redis-cli PING

# Restart Redis
docker-compose restart redis
```

### Issue: Module Not Found
```bash
# Install dependencies
cd /home/duc/analytics
pip install -r shared/requirements-base.txt
pip install -r user-service/requirements.txt
pip install -r api-gateway/requirements.txt
# ... etc for each service
```

---

## 📊 Monitoring

### View Logs
```bash
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f postgres
docker-compose logs -f kafka
```

### Check Database
```bash
# Connect to PostgreSQL
docker exec -it crypto-postgres psql -U crypto_user -d crypto_db

# List tables
\dt

# Query users
SELECT * FROM users;

# Query coins
SELECT * FROM coins;

# Exit
\q
```

### Check Redis
```bash
# Connect to Redis
docker exec -it crypto-redis redis-cli

# Check keys
KEYS *

# Get a value
GET price:bitcoin

# Exit
exit
```

---

## 🎯 Quick Reference

### Infrastructure Ports
- PostgreSQL: `5432`
- Redis: `6379`
- Kafka: `9092`
- Zookeeper: `2181`

### Service Ports
- API Gateway: `8000`
- User Service: `8001`
- Market Data: `8002`
- Analytics: `8003`
- Sentiment: `8004`
- Portfolio: `8005`
- Frontend: `3000`

### Database Credentials
- Host: `localhost`
- Port: `5432`
- Database: `crypto_db`
- User: `crypto_user`
- Password: `crypto_password`

### Environment Variables
```bash
export DATABASE_URL="postgresql://crypto_user:crypto_password@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379/0"
export KAFKA_BROKERS="localhost:9092"
export JWT_SECRET_KEY="your-secret-key-change-in-production"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRATION_HOURS="24"
```

---

## ✅ Success Checklist

- [ ] Docker infrastructure running (PostgreSQL, Redis, Kafka)
- [ ] Database schema initialized
- [ ] Seed data loaded (10 coins)
- [ ] API Gateway running on port 8000
- [ ] User Service running on port 8001
- [ ] Other services running (optional for basic testing)
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Health checks passing

---

**Current Status:** Infrastructure ✅ Ready | Services ⏳ Waiting to Start

**Next Step:** Start services using the commands above or run `./start_services.sh`
