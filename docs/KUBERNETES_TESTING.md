# Kubernetes Deployment Testing Guide

**Status**: Completed  
**Last Updated**: October 25, 2025  
**Version**: 1.0

---

## Table of Contents

1. [Minikube Setup](#minikube-setup)
2. [Resource Configuration](#resource-configuration)
3. [Health Checks](#health-checks)
4. [Testing Procedures](#testing-procedures)
5. [Deployment Verification](#deployment-verification)
6. [Troubleshooting](#troubleshooting)

---

## Minikube Setup

### Installation

```bash
# macOS
brew install minikube

# Linux
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Windows (using Chocolatey)
choco install minikube
```

### Start Minikube Cluster

```bash
# Start with sufficient resources
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=50g \
  --kubernetes-version=v1.28.0

# Or using Docker driver (recommended)
minikube start \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --disk-size=50g

# Enable required addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard
```

### Verify Setup

```bash
# Check cluster status
minikube status

# Get cluster info
kubectl cluster-info
kubectl get nodes

# Start dashboard
minikube dashboard
```

---

## Resource Configuration

### CPU and Memory Requests/Limits

All deployments should specify resource requirements:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  template:
    spec:
      containers:
      - name: api-gateway
        resources:
          requests:
            cpu: 500m          # Minimum needed to schedule
            memory: 512Mi
          limits:
            cpu: 1000m         # Maximum allowed
            memory: 1Gi
```

### Resource Allocation by Service

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| API Gateway | 500m | 1000m | 512Mi | 1Gi |
| User Service | 500m | 1000m | 512Mi | 1Gi |
| Market Data | 1000m | 2000m | 1Gi | 2Gi |
| Analytics | 2000m | 4000m | 2Gi | 4Gi |
| Sentiment | 1000m | 2000m | 2Gi | 4Gi |
| Portfolio | 500m | 1000m | 512Mi | 1Gi |
| Frontend | 200m | 500m | 256Mi | 512Mi |

### Total Requirements for Minikube

- **CPU**: 7.2 cores (request) + buffer = 8 cores minimum
- **Memory**: 8.5 GB (request) + buffer = 12 GB ideal
- **Storage**: 50+ GB for all services and data

### Example Resource-Limited Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-service
  namespace: crypto-analytics
spec:
  replicas: 2
  selector:
    matchLabels:
      app: analytics-service
  template:
    metadata:
      labels:
        app: analytics-service
    spec:
      containers:
      - name: analytics-service
        image: analytics-service:latest
        ports:
        - containerPort: 8003
        resources:
          requests:
            cpu: 2000m
            memory: 2Gi
          limits:
            cpu: 4000m
            memory: 4Gi
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        volumeMounts:
        - name: config
          mountPath: /etc/config
      volumes:
      - name: config
        configMap:
          name: app-config
```

---

## Health Checks

### Liveness Probe

Restarts container if it becomes unresponsive:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
    scheme: HTTP
  initialDelaySeconds: 30    # Wait before first check
  periodSeconds: 10           # Check every 10 seconds
  timeoutSeconds: 5           # Timeout after 5 seconds
  failureThreshold: 3         # Restart after 3 failures
```

### Readiness Probe

Removes from load balancing if not ready:

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
    scheme: HTTP
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Startup Probe

Allows time for container startup:

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  failureThreshold: 30
  periodSeconds: 10
```

### Full Health Check Configuration

```yaml
containers:
- name: api-gateway
  image: api-gateway:latest
  ports:
  - containerPort: 8000
    name: http
  
  # Liveness: restart if hung
  livenessProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
  
  # Readiness: remove from service if unhealthy
  readinessProbe:
    httpGet:
      path: /ready
      port: http
    initialDelaySeconds: 10
    periodSeconds: 5
    timeoutSeconds: 3
    failureThreshold: 3
  
  # Startup: allow time for initialization
  startupProbe:
    httpGet:
      path: /health
      port: http
    failureThreshold: 30
    periodSeconds: 10
```

---

## Testing Procedures

### 1. Deploy to Minikube

```bash
# Create namespace
kubectl create namespace crypto-analytics

# Apply infrastructure manifests (order matters)
kubectl apply -f k8s/01-infrastructure.yaml -n crypto-analytics
sleep 30  # Wait for databases to start

# Check database pods
kubectl get pods -n crypto-analytics
kubectl logs -f postgres-0 -n crypto-analytics

# Apply services
kubectl apply -f k8s/02-services.yaml -n crypto-analytics

# Apply ingress
kubectl apply -f k8s/03-ingress.yaml -n crypto-analytics

# Apply Kafka
kubectl apply -f k8s/04-kafka.yaml -n crypto-analytics
sleep 20

# Apply monitoring
kubectl apply -f k8s/06-monitoring.yaml -n crypto-analytics

# Apply application services (in dependency order)
kubectl apply -f k8s/05-portfolio-monitoring.yaml -n crypto-analytics
```

### 2. Verify Pod Readiness

```bash
# Check all pods are running
kubectl get pods -n crypto-analytics -w

# Expected output (all Running, Ready 1/1 or 2/2):
NAME                                 READY   STATUS    RESTARTS   AGE
postgres-0                           1/1     Running   0          2m
redis-0                              1/1     Running   0          2m
kafka-0                              1/1     Running   0          1m
kafka-1                              1/1     Running   0          1m
kafka-2                              1/1     Running   0          1m
api-gateway-5c7d9f8b2-xyz           2/2     Running   0          30s
user-service-7d8e9f0c3-abc          1/1     Running   0          25s
market-data-service-8e9f0g1d4-def   1/1     Running   0          20s
analytics-service-9f0g1h2e5-ghi     1/1     Running   0          15s
```

### 3. Port Forwarding for Testing

```bash
# Forward API Gateway
kubectl port-forward -n crypto-analytics svc/api-gateway 8000:80 &

# Forward Grafana
kubectl port-forward -n crypto-analytics svc/grafana 3000:3000 &

# Forward Prometheus
kubectl port-forward -n crypto-analytics svc/prometheus 9090:9090 &

# Forward PostgreSQL for debugging
kubectl port-forward -n crypto-analytics svc/postgres 5432:5432 &
```

### 4. Test API Connectivity

```bash
# Get API Gateway service IP
kubectl get svc -n crypto-analytics

# Test health endpoint
curl http://localhost:8000/health

# Test authentication
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!"
  }'

# Test WebSocket
wscat -c ws://localhost:8000/ws/prices?coins=bitcoin,ethereum
```

### 5. Load Testing

```bash
# Run k6 load tests against minikube
k6 run tests/load_tests.js \
  --vus=10 \
  --duration=30s \
  -e API_URL=http://localhost:8000

# Expected: no errors, latency < 500ms p95
```

### 6. Scaling Tests

```bash
# Scale API Gateway to 3 replicas
kubectl scale deployment api-gateway \
  -n crypto-analytics \
  --replicas=3

# Watch replicas spin up
kubectl get pods -n crypto-analytics -w

# Scale Analytics to 5 replicas
kubectl scale deployment analytics-service \
  -n crypto-analytics \
  --replicas=5

# Verify load balancing
kubectl get pods -n crypto-analytics -l app=analytics-service
```

### 7. Failure Simulation

```bash
# Delete a pod (should be auto-replaced)
kubectl delete pod analytics-service-xxxxx \
  -n crypto-analytics

# Watch it restart
kubectl get pods -n crypto-analytics -w

# Kill a service (test failover)
kubectl set env deployment api-gateway \
  KILL_SWITCH=true \
  -n crypto-analytics

# Watch readiness probes trigger
kubectl describe pod api-gateway-xxxxx -n crypto-analytics

# Restore
kubectl set env deployment api-gateway \
  KILL_SWITCH=false \
  -n crypto-analytics
```

---

## Deployment Verification

### Checklist

- [ ] All pods in Running state
- [ ] All pods in Ready state (READY column = X/X)
- [ ] No CrashLoopBackOff or Pending pods
- [ ] Liveness probes passing
- [ ] Readiness probes passing
- [ ] API endpoints responding (< 200ms)
- [ ] WebSocket connections stable
- [ ] Load tests passing
- [ ] Scaling works (pods start and stop correctly)
- [ ] Resource limits respected
- [ ] Logs available via kubectl logs
- [ ] Metrics available in Prometheus
- [ ] Grafana dashboards working

### Commands to Verify

```bash
# Get detailed pod status
kubectl describe pod <pod-name> -n crypto-analytics

# Check pod events
kubectl get events -n crypto-analytics --sort-by='.lastTimestamp'

# View resource usage
kubectl top pods -n crypto-analytics
kubectl top nodes

# Check logs
kubectl logs -f <pod-name> -n crypto-analytics

# Get resource details
kubectl get resources -n crypto-analytics --all-types

# Check ingress
kubectl get ingress -n crypto-analytics -o wide
kubectl describe ingress api-ingress -n crypto-analytics
```

---

## Troubleshooting

### Pod Won't Start

```bash
# Check pod status
kubectl describe pod <pod-name> -n crypto-analytics

# Check logs
kubectl logs <pod-name> -n crypto-analytics --previous

# Common causes:
# - Image pull failed: Check image registry
# - Resource unavailable: Increase Minikube memory/CPU
# - Dependency not ready: Check other services
```

### Service Not Reachable

```bash
# Verify service exists
kubectl get svc -n crypto-analytics

# Check endpoints
kubectl get endpoints -n crypto-analytics

# Test connectivity from pod
kubectl exec -it <pod-name> -n crypto-analytics -- \
  curl http://api-gateway:8000/health

# Check network policies
kubectl get networkpolicies -n crypto-analytics
```

### High Resource Usage

```bash
# Check resource consumption
kubectl top pods -n crypto-analytics --sort-by=memory

# Adjust limits if needed
kubectl set resources deployment <app-name> \
  --limits=cpu=2000m,memory=2Gi \
  -n crypto-analytics

# Restart pods to apply changes
kubectl rollout restart deployment <app-name> \
  -n crypto-analytics
```

### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl get pods -n crypto-analytics -l app=postgres

# Test connection
kubectl exec -it postgres-0 -n crypto-analytics -- \
  psql -U crypto_user -d crypto_db -c "SELECT version();"

# Check Redis
kubectl get pods -n crypto-analytics -l app=redis

# Test Redis connection
kubectl exec -it redis-0 -n crypto-analytics -- \
  redis-cli ping
```

### Kafka Issues

```bash
# Check Kafka pods
kubectl get pods -n crypto-analytics -l app=kafka

# Check Kafka logs
kubectl logs kafka-0 -n crypto-analytics

# Test Kafka connectivity
kubectl exec -it kafka-0 -n crypto-analytics -- \
  kafka-broker-api-versions.sh --bootstrap-server localhost:9092
```

---

## Production Checklist

- [ ] Resource requests/limits configured for all services
- [ ] Liveness/readiness probes configured
- [ ] Startup probes for services with slow initialization
- [ ] Health check endpoints implemented
- [ ] Graceful shutdown (SIGTERM handlers)
- [ ] Circuit breakers for external API calls
- [ ] Retry logic with exponential backoff
- [ ] Connection pooling configured
- [ ] Timeouts set appropriately
- [ ] Monitoring and alerting active
- [ ] Logging configured
- [ ] Secrets management in place
- [ ] RBAC policies configured
- [ ] Network policies defined
- [ ] Pod disruption budgets set
- [ ] Horizontal pod autoscalers configured

---

**Testing Status**: ✅ Ready for Minikube Testing  
**Deployment Target**: Production-grade Kubernetes

---

*Last Updated: October 25, 2025*
