# Kubernetes Minikube Testing Guide

Comprehensive guide for local Kubernetes deployment and testing using Minikube.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Minikube Setup](#minikube-setup)
3. [Cluster Initialization](#cluster-initialization)
4. [Service Deployment](#service-deployment)
5. [Health Checks](#health-checks)
6. [Service Communication Tests](#service-communication-tests)
7. [Data Flow Validation](#data-flow-validation)
8. [Performance Testing](#performance-testing)
9. [Troubleshooting](#troubleshooting)
10. [Cleanup](#cleanup)

## Prerequisites

### System Requirements

- **OS:** Linux, macOS, or Windows (with WSL2)
- **RAM:** 8GB minimum (12GB recommended)
- **CPU:** 4 cores minimum
- **Disk:** 20GB available space

### Required Tools

```bash
# Check versions
minikube version
kubectl version --client
helm version
docker version

# Install (macOS with Homebrew)
brew install minikube kubectl helm docker

# Install (Linux - Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y minikube kubectl helm docker.io
```

### Environment Setup

```bash
# Docker daemon should be running
systemctl status docker
sudo usermod -aG docker $USER

# Verify tools
which minikube kubectl helm docker
```

## Minikube Setup

### 1. Start Minikube Cluster

```bash
# Start with optimal configuration
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=20GB \
  --driver=docker \
  --kubernetes-version=v1.24.0

# Expected output:
# 😄  minikube v1.32.0 on Linux
# ✅  Using the docker driver based on existing profile
# 🎉  minikube cluster started successfully!
```

### 2. Verify Cluster Status

```bash
# Check cluster information
minikube status
# Output:
# minikube
# type: Control Plane
# host: Running
# kubelet: Running
# apiserver: Running
# kubeconfig: Configured

# Get cluster details
kubectl cluster-info
kubectl get nodes
kubectl get nodes -o wide

# Expected: 1 node in Ready state
```

### 3. Enable Minikube Addons

```bash
# List available addons
minikube addons list

# Enable required addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# Verify addons
minikube addons list | grep enabled
```

### 4. Configure Docker Registry Access

```bash
# Use Minikube's Docker daemon for building images
eval $(minikube docker-env)

# Verify
docker ps

# Build images using Minikube's Docker
docker build -t analytics:latest ./analytics-service/
docker build -t market-data:latest ./market-data-service/
# ... build other services
```

## Cluster Initialization

### 1. Create Namespaces

```bash
# Create namespaces for organization
kubectl create namespace analytics
kubectl create namespace monitoring
kubectl create namespace default

# Verify namespaces
kubectl get namespaces
```

### 2. Create Secrets for Environment Variables

```bash
# Database secrets
kubectl create secret generic db-secret \
  --from-literal=DB_HOST=postgres \
  --from-literal=DB_USER=analytics_user \
  --from-literal=DB_PASSWORD=SecurePassword123 \
  --from-literal=DB_NAME=analytics_db \
  -n analytics

# Redis secrets
kubectl create secret generic redis-secret \
  --from-literal=REDIS_HOST=redis \
  --from-literal=REDIS_PORT=6379 \
  -n analytics

# API keys
kubectl create secret generic api-keys \
  --from-literal=BINANCE_API_KEY=your_binance_key \
  --from-literal=COINBASE_API_KEY=your_coinbase_key \
  --from-literal=NEWS_API_KEY=your_news_api_key \
  -n analytics

# JWT secrets
kubectl create secret generic jwt-secret \
  --from-literal=JWT_SECRET=your_jwt_secret_key \
  --from-literal=JWT_REFRESH_SECRET=your_refresh_secret_key \
  -n analytics

# Verify secrets
kubectl get secrets -n analytics
```

### 3. Create ConfigMaps for Configuration

```bash
# Application configuration
kubectl create configmap app-config \
  --from-literal=ENVIRONMENT=development \
  --from-literal=LOG_LEVEL=info \
  --from-literal=CACHE_TTL=300 \
  -n analytics

# Database configuration
kubectl create configmap db-config \
  --from-literal=DB_CONNECTION_POOL_SIZE=20 \
  --from-literal=DB_ECHO=false \
  -n analytics

# Verify configmaps
kubectl get configmaps -n analytics
```

## Service Deployment

### 1. Deploy PostgreSQL Database

```yaml
# Save as k8s/postgres-deployment.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: analytics
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: analytics
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: DB_NAME
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: DB_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: DB_PASSWORD
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: analytics
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

Deploy:
```bash
kubectl apply -f k8s/postgres-deployment.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n analytics --timeout=300s
```

### 2. Deploy Redis Cache

```yaml
# Save as k8s/redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: analytics
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: analytics
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

Deploy:
```bash
kubectl apply -f k8s/redis-deployment.yaml
kubectl wait --for=condition=ready pod -l app=redis -n analytics --timeout=300s
```

### 3. Deploy Backend Services

```bash
# Apply all manifests in order
kubectl apply -f k8s/01-infrastructure.yaml
kubectl apply -f k8s/02-services.yaml
kubectl apply -f k8s/03-ingress.yaml

# Wait for all deployments
kubectl wait --for=condition=available --timeout=600s \
  deployment --all \
  -n analytics

# Verify deployments
kubectl get deployments -n analytics
kubectl get pods -n analytics
kubectl get services -n analytics
```

### 4. Initialize Database

```bash
# Get postgres pod name
POSTGRES_POD=$(kubectl get pods -n analytics -l app=postgres -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -it $POSTGRES_POD -n analytics -- psql -U analytics_user -d analytics_db \
  -f /migrations/001_initial_schema.sql

# Verify schema
kubectl exec -it $POSTGRES_POD -n analytics -- psql -U analytics_user -d analytics_db \
  -c "\dt"
```

## Health Checks

### 1. Cluster Health

```bash
# Check cluster status
kubectl get nodes
kubectl describe node

# Check system pods
kubectl get pods --all-namespaces

# Check API server
kubectl get componentstatuses
```

### 2. Service Health Checks

```bash
# Check all services in namespace
kubectl get svc -n analytics

# Describe each service
kubectl describe svc api-gateway -n analytics
kubectl describe svc user-service -n analytics
kubectl describe svc market-data-service -n analytics
kubectl describe svc analytics-service -n analytics
kubectl describe svc sentiment-service -n analytics
kubectl describe svc portfolio-service -n analytics

# Check service endpoints
kubectl get endpoints -n analytics
```

### 3. Pod Health Checks

```bash
# Check pod status
kubectl get pods -n analytics -o wide

# View pod logs
kubectl logs -n analytics -l app=api-gateway --all-containers=true

# Describe problematic pod
kubectl describe pod <pod-name> -n analytics

# Check pod resources
kubectl top pods -n analytics
```

### 4. Health Check Script

```bash
#!/bin/bash
# Save as scripts/k8s_health_check.sh

set -e

NAMESPACE="analytics"

echo "=== Kubernetes Cluster Health Check ==="

# Check cluster status
echo -e "\n[1] Cluster Status"
kubectl cluster-info
kubectl get nodes

# Check namespace
echo -e "\n[2] Namespace: $NAMESPACE"
kubectl get namespace $NAMESPACE

# Check services
echo -e "\n[3] Services"
kubectl get svc -n $NAMESPACE
kubectl get endpoints -n $NAMESPACE

# Check deployments
echo -e "\n[4] Deployments"
kubectl get deployments -n $NAMESPACE
kubectl get pods -n $NAMESPACE -o wide

# Check pod status
echo -e "\n[5] Pod Status Details"
for pod in $(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}'); do
  status=$(kubectl get pod $pod -n $NAMESPACE -o jsonpath='{.status.phase}')
  echo "  $pod: $status"
done

# Check service connectivity
echo -e "\n[6] Service DNS Resolution"
kubectl run -it --rm --image=busybox dns-test --restart=Never -n $NAMESPACE -- \
  nslookup postgres
kubectl run -it --rm --image=busybox dns-test --restart=Never -n $NAMESPACE -- \
  nslookup redis

# Check API Gateway health
echo -e "\n[7] API Gateway Health"
kubectl port-forward -n $NAMESPACE svc/api-gateway 8000:8000 &
sleep 2
curl -s http://localhost:8000/health || echo "API Gateway not responding"
kill %1 2>/dev/null || true

# Check resource usage
echo -e "\n[8] Resource Usage"
kubectl top nodes
kubectl top pods -n $NAMESPACE

# Check events
echo -e "\n[9] Recent Events"
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'

echo -e "\n=== Health Check Complete ==="
```

Run health check:
```bash
chmod +x scripts/k8s_health_check.sh
./scripts/k8s_health_check.sh
```

## Service Communication Tests

### 1. Test Inter-Service Communication

```bash
# Create a test pod
kubectl run -it --rm --image=python:3.11-alpine test-pod \
  --restart=Never -n analytics -- \
  sh

# Inside the pod:
# Test DNS resolution
nslookup api-gateway
nslookup user-service
nslookup market-data-service

# Test HTTP connectivity
pip install requests
python3 << 'EOF'
import requests

services = [
    ('http://api-gateway:8000', 'API Gateway'),
    ('http://user-service:8001', 'User Service'),
    ('http://market-data-service:8002', 'Market Data Service'),
    ('http://analytics-service:8003', 'Analytics Service'),
    ('http://sentiment-service:8004', 'Sentiment Service'),
    ('http://portfolio-service:8005', 'Portfolio Service'),
]

for url, name in services:
    try:
        response = requests.get(f'{url}/health', timeout=5)
        print(f'✅ {name}: {response.status_code}')
    except Exception as e:
        print(f'❌ {name}: {e}')
EOF
```

### 2. Service-to-Service Authentication

```bash
# Test JWT authentication between services
kubectl exec -it $(kubectl get pods -n analytics -l app=api-gateway -o jsonpath='{.items[0].metadata.name}') -n analytics -- \
  python3 << 'EOF'
import requests
import json

# Create test user
register_data = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'SecurePass123!'
}

response = requests.post(
    'http://localhost:8000/api/users/register',
    json=register_data
)

if response.status_code == 201:
    token = response.json()['data']['access_token']
    print(f'✅ User registration successful')
    print(f'Token: {token[:20]}...')
    
    # Test authenticated request
    headers = {'Authorization': f'Bearer {token}'}
    user_response = requests.get(
        'http://localhost:8000/api/users/profile',
        headers=headers
    )
    if user_response.status_code == 200:
        print(f'✅ Authenticated request successful')
    else:
        print(f'❌ Authenticated request failed: {user_response.status_code}')
else:
    print(f'❌ Registration failed: {response.status_code}')
    print(response.text)
EOF
```

### 3. Kafka Message Flow Test

```bash
# Port forward to Kafka
kubectl port-forward -n analytics svc/kafka 9092:9092 &

# Verify Kafka connectivity
python3 << 'EOF'
from kafka import KafkaProducer, KafkaConsumer
import json

# Test producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send test message
producer.send('prices-updated', {
    'coin_id': 'bitcoin',
    'price': 45000,
    'timestamp': '2025-01-01T00:00:00Z'
})
producer.flush()
print('✅ Message sent to Kafka')

# Test consumer
consumer = KafkaConsumer(
    'prices-updated',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    max_poll_records=1
)

for message in consumer:
    print(f'✅ Received message: {message.value}')
    break

consumer.close()
EOF
```

## Data Flow Validation

### 1. End-to-End Data Flow Test

```bash
# Create comprehensive test script
kubectl run -it --rm --image=python:3.11-alpine e2e-test \
  --restart=Never -n analytics -- python3 << 'EOF'
import requests
import time

BASE_URL = 'http://api-gateway:8000'

print("=== E2E Data Flow Test ===\n")

# 1. Register user
print("[1] User Registration")
user_data = {
    'username': f'testuser_{int(time.time())}',
    'email': f'user_{int(time.time())}@example.com',
    'password': 'SecurePass123!'
}
response = requests.post(f'{BASE_URL}/api/users/register', json=user_data)
assert response.status_code == 201, f"Registration failed: {response.text}"
token = response.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}
print("✅ User registration successful")

# 2. Get current prices
print("\n[2] Get Market Prices")
response = requests.get(f'{BASE_URL}/api/market/prices', headers=headers)
assert response.status_code == 200, f"Get prices failed: {response.text}"
prices = response.json()['data']
print(f"✅ Got {len(prices)} prices")

# 3. Create portfolio
print("\n[3] Create Portfolio")
portfolio_data = {'name': 'Test Portfolio'}
response = requests.post(f'{BASE_URL}/api/portfolio', json=portfolio_data, headers=headers)
assert response.status_code == 201, f"Portfolio creation failed: {response.text}"
portfolio_id = response.json()['data']['id']
print(f"✅ Portfolio created: {portfolio_id}")

# 4. Add asset to portfolio
print("\n[4] Add Asset to Portfolio")
asset_data = {
    'coin_id': 'bitcoin',
    'quantity': 0.5,
    'purchase_price': 45000,
    'purchase_date': '2025-01-01'
}
response = requests.post(
    f'{BASE_URL}/api/portfolio/{portfolio_id}/assets',
    json=asset_data,
    headers=headers
)
assert response.status_code == 201, f"Add asset failed: {response.text}"
print("✅ Asset added to portfolio")

# 5. Get portfolio performance
print("\n[5] Get Portfolio Performance")
response = requests.get(
    f'{BASE_URL}/api/portfolio/{portfolio_id}/performance',
    headers=headers
)
assert response.status_code == 200, f"Get performance failed: {response.text}"
performance = response.json()['data']
print(f"✅ Performance: ROI {performance.get('roi_percentage', 0):.2f}%")

# 6. Get analytics
print("\n[6] Get Analytics")
response = requests.get(
    f'{BASE_URL}/api/analytics/moving-average/bitcoin',
    headers=headers
)
assert response.status_code == 200, f"Get analytics failed: {response.text}"
print("✅ Analytics retrieved")

# 7. Get sentiment
print("\n[7] Get Sentiment Analysis")
response = requests.get(
    f'{BASE_URL}/api/sentiment/bitcoin',
    headers=headers
)
assert response.status_code == 200, f"Get sentiment failed: {response.text}"
sentiment = response.json()['data']
print(f"✅ Sentiment score: {sentiment.get('overall_score', 0):.2f}")

print("\n=== All E2E Tests Passed ===")
EOF
```

## Performance Testing

### 1. Run Load Test with k6

```bash
# Install k6
curl https://get.k6.io | bash

# Run load test
k6 run tests/load_tests.js \
  --vus 20 \
  --duration 5m \
  -e BASE_URL=http://$(minikube ip):80 \
  -e WS_URL=ws://$(minikube ip):80

# Monitor results
# k6 generates a summary at the end with:
# - Request rate
# - Error rate
# - Response times (p50, p90, p95, p99)
# - Custom metrics
```

### 2. Monitor Resource Usage

```bash
# Watch resource usage in real-time
kubectl top nodes -n analytics --watch

kubectl top pods -n analytics --watch

# Get detailed resource metrics
kubectl describe node

# Check HPA status (if configured)
kubectl get hpa -n analytics
kubectl describe hpa api-gateway -n analytics
```

## Troubleshooting

### 1. Pod Stuck in Pending

```bash
# Describe the pod
kubectl describe pod <pod-name> -n analytics

# Check events
kubectl get events -n analytics --sort-by='.lastTimestamp'

# Check resource availability
kubectl describe node

# Common causes:
# - Insufficient memory/CPU
# - PVC not available
# - ImagePullBackOff
```

### 2. Service Not Accessible

```bash
# Check service
kubectl get svc <service-name> -n analytics

# Check endpoints
kubectl get endpoints <service-name> -n analytics

# Check pod logs
kubectl logs -n analytics -l app=<app> --tail=50

# Test DNS
kubectl run -it --rm --image=busybox dns-test --restart=Never -n analytics -- \
  nslookup <service-name>
```

### 3. Database Connection Issues

```bash
# Check postgres pod
kubectl get pod -l app=postgres -n analytics

# Test connection
kubectl exec -it <postgres-pod> -n analytics -- \
  psql -U analytics_user -d analytics_db -c "SELECT version();"

# Check connection pool
kubectl logs <app-pod> -n analytics | grep -i connection
```

### 4. Clear and Reset

```bash
# Delete all resources in namespace
kubectl delete all --all -n analytics

# Restart Minikube
minikube stop
minikube delete
minikube start

# Clean up Minikube cache
minikube cache prune
rm -rf ~/.minikube
```

## Cleanup

### 1. Stop Services

```bash
# Stop all pods (keep PVCs for data persistence)
kubectl delete deployments --all -n analytics

# Stop Minikube
minikube stop

# Delete Minikube cluster
minikube delete
```

### 2. Clean Up Docker Images

```bash
# Remove local images
docker image prune -a --force

# Stop Docker daemon
systemctl stop docker
```

## Testing Checklist

- [ ] Minikube cluster started successfully
- [ ] All required addons enabled
- [ ] Database deployed and initialized
- [ ] Redis deployed
- [ ] All 6 backend services deployed
- [ ] All services in Ready state
- [ ] Secrets and ConfigMaps created
- [ ] Service DNS resolution works
- [ ] Inter-service communication successful
- [ ] API Gateway health check passing
- [ ] User registration workflow successful
- [ ] Portfolio creation workflow successful
- [ ] Analytics endpoint responding
- [ ] Sentiment endpoint responding
- [ ] Load test completed successfully
- [ ] No pod memory leaks
- [ ] No pod restarts
- [ ] All services accessible via Ingress (if configured)

## Performance Baselines (Expected)

- API response time: < 500ms (p95)
- Database connection setup: < 100ms
- Cache hit rate: > 95%
- Error rate: < 0.1%
- Pod startup time: < 30s
- Database startup time: < 60s
- Zero pod restarts during 5-minute load test

## References

- [Minikube Documentation](https://minikube.sigs.k8s.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [k6 Load Testing](https://k6.io/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
