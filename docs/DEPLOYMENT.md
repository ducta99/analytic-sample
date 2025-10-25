# Deployment Guide

**Version**: 1.0  
**Last Updated**: October 25, 2025  
**Status**: Production Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development Setup](#local-development-setup)
3. [Docker Compose Deployment](#docker-compose-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Environment Variables](#environment-variables)
6. [Database Migrations](#database-migrations)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose (v20.10+)
- Kubernetes 1.24+ (for K8s deployment)
- kubectl (v1.24+)
- Python 3.11+
- Node.js 18+
- Git

### Get Started in 5 Minutes

```bash
# Clone the repository
git clone https://github.com/your-org/crypto-analytics.git
cd crypto-analytics

# Copy environment file
cp .env.example .env

# Start with Docker Compose
docker-compose up -d

# Wait for services to be ready
sleep 30

# Check health
curl http://localhost:8000/health

# Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## Local Development Setup

### Setup Development Environment

```bash
# Install Python dependencies
cd api-gateway
pip install -r requirements.txt
pip install -r ../shared/requirements-base.txt

# Install Node dependencies
cd frontend
npm install

# Create database
createdb crypto_db
psql crypto_db < ../migrations/001_initial_schema.sql

# Start services individually
# Terminal 1: API Gateway
cd api-gateway
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Other services (see docker-compose.yml)
docker-compose up postgres redis kafka
```

### Development Workflow

```bash
# Run tests
pytest tests/ -v --cov

# Check code formatting
black . --check
isort . --check-only

# Type checking
mypy . --ignore-missing-imports

# Lint code
pylint app/

# Run E2E tests
pytest tests/e2e_tests.py -v
```

---

## Docker Compose Deployment

### Environment Setup

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://crypto_user:crypto_password@postgres:5432/crypto_db
POSTGRES_USER=crypto_user
POSTGRES_PASSWORD=crypto_password
POSTGRES_DB=crypto_db

# Redis
REDIS_URL=redis://redis:6379/0

# Kafka
KAFKA_BROKERS=kafka:9092
KAFKA_TOPIC_PRICES=price_updates
KAFKA_TOPIC_SENTIMENT=sentiment_updates

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API Keys
BINANCE_API_KEY=your_key_here
COINBASE_API_KEY=your_key_here
NEWSAPI_KEY=your_key_here

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=False
```

### Deploy with Docker Compose

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

### Health Check

```bash
# Check API Gateway
curl http://localhost:8000/health

# Check all services
docker-compose ps

# View specific service logs
docker-compose logs api-gateway
docker-compose logs market-data-service
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
brew install kubectl  # macOS
# or use official installers for other OS

# Verify kubectl installation
kubectl version --client

# Verify cluster connection
kubectl cluster-info

# Create namespace
kubectl create namespace crypto-analytics
```

### Deploy to Kubernetes

```bash
# Apply infrastructure manifests
kubectl apply -f k8s/01-infrastructure.yaml

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod \
  -l app=postgres \
  -n crypto-analytics \
  --timeout=300s

# Apply services
kubectl apply -f k8s/02-services.yaml

# Apply ingress
kubectl apply -f k8s/03-ingress.yaml

# Apply Kafka
kubectl apply -f k8s/04-kafka.yaml

# Apply monitoring stack
kubectl apply -f k8s/05-portfolio-monitoring.yaml
kubectl apply -f k8s/06-monitoring.yaml
kubectl apply -f k8s/07-grafana.yaml

# Verify deployments
kubectl get deployments -n crypto-analytics
kubectl get pods -n crypto-analytics
```

### Monitoring Kubernetes

```bash
# Watch pod status
kubectl get pods -n crypto-analytics -w

# Get pod details
kubectl describe pod <pod-name> -n crypto-analytics

# View pod logs
kubectl logs <pod-name> -n crypto-analytics

# View logs from all containers in a pod
kubectl logs <pod-name> -n crypto-analytics --all-containers=true

# Port forward to local
kubectl port-forward -n crypto-analytics svc/api-gateway 8000:8000
kubectl port-forward -n crypto-analytics svc/grafana 3000:3000

# Get service endpoints
kubectl get svc -n crypto-analytics
```

### Update Deployments

```bash
# Update single service image
kubectl set image deployment/api-gateway \
  api-gateway=ghcr.io/your-repo/api_gateway:v1.1.0 \
  -n crypto-analytics

# Verify rollout status
kubectl rollout status deployment/api-gateway -n crypto-analytics

# Rollback if needed
kubectl rollout undo deployment/api-gateway -n crypto-analytics

# View rollout history
kubectl rollout history deployment/api-gateway -n crypto-analytics
```

### Scaling

```bash
# Scale deployment
kubectl scale deployment api-gateway --replicas=5 -n crypto-analytics

# Auto-scale with HPA
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: crypto-analytics
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF
```

---

## Environment Variables

### Core Configuration

```
# Environment
ENVIRONMENT=production          # development, staging, production
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
DEBUG=False

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
CORS_ORIGINS=http://localhost:3000,https://example.com
```

### Database

```
DATABASE_URL=postgresql://user:password@host:5432/database
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
```

### Cache

```
REDIS_URL=redis://host:6379/0
REDIS_PASSWORD=
REDIS_SSL=False
CACHE_TTL_PRICES=10
CACHE_TTL_ANALYTICS=300
CACHE_TTL_SENTIMENT=300
```

### Message Queue

```
KAFKA_BROKERS=broker1:9092,broker2:9092,broker3:9092
KAFKA_TOPIC_PRICES=price_updates
KAFKA_TOPIC_SENTIMENT=sentiment_updates
KAFKA_GROUP_ID=analytics-service
KAFKA_AUTO_OFFSET_RESET=earliest
```

### External APIs

```
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
BINANCE_WS_URL=wss://stream.binance.com:9443/ws

COINBASE_API_KEY=your_key
COINBASE_API_SECRET=your_secret

NEWSAPI_KEY=your_key
NEWSAPI_BASE_URL=https://newsapi.org/v2

HUGGINGFACE_MODEL=distilbert-base-uncased-finetuned-sst-2-english
```

### Monitoring

```
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
LOKI_URL=http://loki:3100
SLACK_WEBHOOK=https://hooks.slack.com/services/your/webhook
```

---

## Database Migrations

### Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE crypto_db;
CREATE USER crypto_user WITH PASSWORD 'secure_password';
ALTER ROLE crypto_user SET client_encoding TO 'utf8';
ALTER ROLE crypto_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE crypto_user SET default_transaction_deferrable TO on;
ALTER ROLE crypto_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE crypto_db TO crypto_user;
\q
```

### Run Migrations

```bash
# Using migration scripts
psql -U crypto_user -d crypto_db -f migrations/001_initial_schema.sql

# Verify schema
psql -U crypto_user -d crypto_db -c "\dt"

# View migration history
psql -U crypto_user -d crypto_db -c "SELECT * FROM schema_migrations;"
```

### Backup Database

```bash
# Full backup
pg_dump -U crypto_user -d crypto_db > backup.sql

# Compressed backup
pg_dump -U crypto_user -d crypto_db | gzip > backup.sql.gz

# Restore from backup
psql -U crypto_user -d crypto_db < backup.sql
gunzip -c backup.sql.gz | psql -U crypto_user -d crypto_db
```

---

## Monitoring & Logging

### Access Monitoring Dashboards

```bash
# Prometheus (metrics)
kubectl port-forward -n crypto-analytics svc/prometheus 9090:9090
# Visit: http://localhost:9090

# Grafana (dashboards)
kubectl port-forward -n crypto-analytics svc/grafana 3000:3000
# Visit: http://localhost:3000 (default: admin/admin)

# Loki (logs)
kubectl port-forward -n crypto-analytics svc/loki 3100:3100
# Visit: http://localhost:3100
```

### Query Metrics

```bash
# CPU usage per pod
kubectl top pods -n crypto-analytics

# Node resource usage
kubectl top nodes

# Get events
kubectl get events -n crypto-analytics --sort-by='.lastTimestamp'
```

### View Logs

```bash
# Tail logs from API Gateway
kubectl logs -f deployment/api-gateway -n crypto-analytics

# Logs from multiple pods
kubectl logs -f -l app=api-gateway -n crypto-analytics

# Previous pod logs
kubectl logs <pod-name> --previous -n crypto-analytics

# Export logs
kubectl logs deployment/api-gateway -n crypto-analytics > api-gateway.log
```

---

## Backup & Recovery

### Database Backup Strategy

```bash
# Daily automated backup
# Add to crontab:
0 2 * * * pg_dump -U crypto_user -d crypto_db | gzip > /backups/crypto_db_$(date +\%Y\%m\%d).sql.gz

# Weekly full backup with retention
find /backups -name "crypto_db_*.sql.gz" -mtime +30 -delete

# Upload to cloud storage
aws s3 cp /backups/crypto_db_$(date +\%Y\%m\%d).sql.gz s3://my-backup-bucket/database/
```

### Redis Backup

```bash
# Manual backup
docker exec crypto-redis redis-cli BGSAVE

# Check backup location
docker exec crypto-redis redis-cli LASTSAVE

# Restore
docker cp dump.rdb crypto-redis:/data/
docker exec crypto-redis redis-cli SHUTDOWN
docker start crypto-redis
```

### Kubernetes Persistent Volume Backup

```bash
# Create snapshot
kubectl snapshot create pvc-snapshot pvc/postgres-data -n crypto-analytics

# List snapshots
kubectl get volumesnapshots -n crypto-analytics

# Restore from snapshot
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data-restored
  namespace: crypto-analytics
spec:
  dataSource:
    name: pvc-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale API Gateway to 5 replicas
kubectl scale deployment api-gateway --replicas=5 -n crypto-analytics

# Scale Analytics Service to 3 replicas
kubectl scale deployment analytics-service --replicas=3 -n crypto-analytics

# View current replica count
kubectl get deployment -n crypto-analytics
```

### Vertical Scaling

```bash
# Update resource requests in deployment
kubectl set resources deployment api-gateway \
  -c=api-gateway \
  --requests=cpu=500m,memory=512Mi \
  --limits=cpu=1000m,memory=1Gi \
  -n crypto-analytics
```

### Database Scaling

```bash
# Increase PostgreSQL shared_buffers
kubectl set env statefulset/postgres \
  POSTGRES_SHARED_BUFFERS=256MB \
  -n crypto-analytics

# Restart for changes to take effect
kubectl rollout restart statefulset/postgres -n crypto-analytics
```

---

## Troubleshooting

### Common Issues

#### Service Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n crypto-analytics

# Check logs
kubectl logs <pod-name> -n crypto-analytics

# Check events
kubectl get events -n crypto-analytics

# Check resource constraints
kubectl get resourcequota -n crypto-analytics
```

#### Database Connection Failed

```bash
# Verify PostgreSQL is running
kubectl get pod -l app=postgres -n crypto-analytics

# Check PostgreSQL logs
kubectl logs -l app=postgres -n crypto-analytics

# Connect to database
kubectl exec -it postgres-0 -n crypto-analytics -- \
  psql -U crypto_user -d crypto_db
```

#### High Memory Usage

```bash
# Check memory per pod
kubectl top pods -n crypto-analytics

# Identify problematic pod
kubectl top pods -n crypto-analytics --sort-by=memory

# Increase pod memory limit
kubectl set resources deployment <deployment> \
  --limits=memory=2Gi \
  -n crypto-analytics

# Restart pod
kubectl rollout restart deployment/<deployment> -n crypto-analytics
```

#### API Latency

```bash
# Check API response times
kubectl logs -l app=api-gateway -n crypto-analytics | grep "response_time"

# Profile with Prometheus
# PromQL: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Check upstream services
kubectl get pods -n crypto-analytics

# Increase API Gateway replicas if needed
kubectl scale deployment api-gateway --replicas=10 -n crypto-analytics
```

### Performance Optimization

```bash
# Enable Redis caching
kubectl set env deployment/api-gateway CACHE_ENABLED=true -n crypto-analytics

# Tune Kafka consumers
kubectl set env deployment/analytics-service \
  KAFKA_FETCH_MIN_BYTES=1024 \
  KAFKA_FETCH_MAX_WAIT_MS=500 \
  -n crypto-analytics

# Increase database connections
kubectl set env deployment/api-gateway \
  DATABASE_POOL_SIZE=20 \
  -n crypto-analytics
```

### Emergency Procedures

```bash
# Restart all services
kubectl rollout restart deployment -n crypto-analytics

# Clear cache
kubectl exec -it redis-0 -n crypto-analytics -- redis-cli FLUSHALL

# Database recovery
# 1. Take backup
pg_dump -U crypto_user -d crypto_db > backup.sql

# 2. Drop and recreate
psql -U crypto_user -c "DROP DATABASE crypto_db;"
psql -U crypto_user -c "CREATE DATABASE crypto_db;"

# 3. Restore
psql -U crypto_user -d crypto_db < backup.sql

# Drain node for maintenance
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Return node to service
kubectl uncordon <node-name>
```

---

## Support

For issues or questions:

- **Documentation**: See `docs/` directory
- **Issues**: Create an issue on GitHub
- **Security**: Report to security@example.com
- **Community**: Slack channel #crypto-analytics

---

**Last Updated**: October 25, 2025  
**Version**: 1.0.0  
**Maintainer**: DevOps Team
