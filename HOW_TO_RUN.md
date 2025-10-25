# 🚀 How to Run the Cryptocurrency Analytics Platform

## Quick Start Guide

### Prerequisites
- ✅ Docker and Docker Compose installed
- ✅ Python 3.11+ with conda/virtualenv
- ✅ Node.js 18+ and npm
- ✅ 8GB+ RAM available

---

## 🔧 Backend (6 Microservices)

### Option 1: Automated Startup (Recommended)

```bash
cd /home/duc/analytics

# Start all backend services
./RUN_BACKEND.sh

# Stop all backend services
./STOP_BACKEND.sh
```

The script will:
1. ✅ Check and start Docker infrastructure (PostgreSQL, Redis, Kafka, Zookeeper)
2. ✅ Set all required environment variables
3. ✅ Start all 6 microservices with proper PYTHONPATH
4. ✅ Run health checks
5. ✅ Display service URLs

### Option 2: Manual Startup

```bash
cd /home/duc/analytics

# 1. Set environment
export PYTHONPATH="/home/duc/analytics:$PYTHONPATH"
export DATABASE_URL="postgresql+asyncpg://crypto_user:crypto_pass@localhost:5432/crypto_db"
export REDIS_URL="redis://localhost:6379"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export JWT_SECRET="your-secret-key-change-in-production"

# 2. Start Docker infrastructure
docker-compose up -d postgres redis kafka zookeeper

# 3. Start services (in separate terminals)
cd api-gateway && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd user-service && uvicorn app.main:app --host 0.0.0.0 --port 8001
cd market-data-service && uvicorn app.main:app --host 0.0.0.0 --port 8002
cd analytics-service && uvicorn app.main:app --host 0.0.0.0 --port 8003
cd sentiment-service && uvicorn app.main:app --host 0.0.0.0 --port 8004
cd portfolio-service && uvicorn app.main:app --host 0.0.0.0 --port 8005
```

### Backend Service URLs

After starting, access the API documentation:

| Service | URL | Status |
|---------|-----|--------|
| **API Gateway** | http://localhost:8000/docs | Main entry point |
| **User Service** | http://localhost:8001/docs | Authentication |
| **Market Data** | http://localhost:8002/docs | Live prices |
| **Analytics** | http://localhost:8003/docs | Technical analysis |
| **Sentiment** | http://localhost:8004/docs | News sentiment |
| **Portfolio** | http://localhost:8005/docs | Portfolio mgmt |

### Health Check

```bash
# Check all services
for port in 8000 8001 8002 8003 8004 8005; do
  echo "Port $port:" && curl http://localhost:$port/health
done
```

---

## 🎨 Frontend (Next.js)

### Option 1: Automated Startup (Recommended)

```bash
cd /home/duc/analytics

# Start frontend development server
./RUN_FRONTEND.sh
```

The script will:
1. ✅ Check Node.js installation
2. ✅ Install npm dependencies (if needed)
3. ✅ Create .env.local with backend URLs
4. ✅ Start Next.js dev server on http://localhost:3000

### Option 2: Manual Startup

```bash
cd /home/duc/analytics/frontend

# 1. Install dependencies (first time only)
npm install --legacy-peer-deps

# 2. Create environment file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8002/ws
NODE_ENV=development
EOF

# 3. Start dev server
npm run dev
```

### Frontend URL

- **Application:** http://localhost:3000
- **Auto-reload:** Enabled (HMR)

---

## 🎯 Complete Workflow

### 1️⃣ Start Backend (Terminal 1)

```bash
cd /home/duc/analytics
./RUN_BACKEND.sh
```

Wait for the health check to show services running.

### 2️⃣ Start Frontend (Terminal 2)

```bash
cd /home/duc/analytics
./RUN_FRONTEND.sh
```

Wait for "Ready on http://localhost:3000"

### 3️⃣ Access the Application

Open your browser and go to: **http://localhost:3000**

---

## 🧪 Testing

### Run End-to-End Tests

```bash
cd /home/duc/analytics
pytest tests/e2e_tests.py -v
```

### Run Load Tests

```bash
cd /home/duc/analytics
k6 run tests/load_tests.js
```

### Run Frontend Tests

```bash
cd frontend
npm run test
npm run type-check
```

---

## 📊 Monitoring

### View Logs

```bash
# All backend services
tail -f /home/duc/analytics/logs/*.log

# Specific service
tail -f /home/duc/analytics/logs/api-gateway.log

# Docker infrastructure
docker logs -f crypto-postgres
docker logs -f crypto-kafka
```

### Check Docker Containers

```bash
docker ps
docker-compose ps
```

### Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

---

## 🛑 Stopping Services

### Stop Backend

```bash
cd /home/duc/analytics
./STOP_BACKEND.sh
```

### Stop Frontend

Press `Ctrl+C` in the terminal running the frontend

### Stop Infrastructure

```bash
docker-compose down
```

---

## ⚠️ Troubleshooting

### Backend Issues

**Problem:** "ModuleNotFoundError: No module named 'shared'"

```bash
# Solution: Set PYTHONPATH
export PYTHONPATH="/home/duc/analytics:$PYTHONPATH"
```

**Problem:** "Connection refused" to services

```bash
# Check if service is running
ps aux | grep uvicorn

# Check logs
tail -f logs/[service-name].log
```

**Problem:** Kafka unhealthy

```bash
# Restart Kafka
docker restart crypto-kafka

# Check status
docker ps | grep kafka
```

### Frontend Issues

**Problem:** "Cannot connect to backend"

```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check .env.local
cat frontend/.env.local

# 3. Restart frontend
cd frontend && npm run dev
```

**Problem:** npm install fails

```bash
# Use legacy peer deps flag
npm install --legacy-peer-deps
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `RUN_BACKEND.sh` | Start all backend services |
| `STOP_BACKEND.sh` | Stop all backend services |
| `RUN_FRONTEND.sh` | Start frontend dev server |
| `docker-compose.yml` | Infrastructure setup |
| `logs/*.log` | Service logs |

---

## 🎉 Success Indicators

You'll know everything is working when:

✅ **Backend:** All 6 services show "HEALTHY" in health check  
✅ **Frontend:** Browser shows dashboard at localhost:3000  
✅ **Docker:** 4 containers running (postgres, redis, kafka, zookeeper)  
✅ **Database:** Seeded with 10 cryptocurrencies  
✅ **Redis:** Caching working with TTL  

---

## 📞 Quick Commands Reference

```bash
# Start everything
./RUN_BACKEND.sh          # Terminal 1
./RUN_FRONTEND.sh         # Terminal 2

# Check status
curl http://localhost:8000/health
curl http://localhost:3000

# View logs
tail -f logs/*.log

# Stop everything
./STOP_BACKEND.sh
# Ctrl+C in frontend terminal

# Full reset
docker-compose down -v
docker-compose up -d
./RUN_BACKEND.sh
```

---

**🚀 You're ready to go! Start with `./RUN_BACKEND.sh` then `./RUN_FRONTEND.sh`**
