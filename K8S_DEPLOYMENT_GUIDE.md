# Kubernetes Deployment Guide for Crypto Analytics Platform

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     KUBERNETES CLUSTER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            INGRESS (nginx) - External Access             │   │
│  │  api.crypto-analytics.com → LoadBalancer:80/443         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         API GATEWAY (3 replicas, HPA 3-10)              │   │
│  │  - Rate limiting (5/min auth, unlimited data)           │   │
│  │  - Request ID middleware                                │   │
│  │  - Route to all backend services                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│    ↙    ↓    ↘    ↓    ↙                                        │
│   ┌────┐  ┌─────────────┐  ┌──────────────┐  ┌────────────┐   │
│   │USER│  │MARKET DATA  │  │ANALYTICS     │  │SENTIMENT   │   │
│   │SVC │  │SERVICE      │  │SERVICE (HPA) │  │SERVICE     │   │
│   │    │  │(2 replicas) │  │(3-10 reps)   │  │(2 reps)    │   │
│   └────┘  └─────────────┘  └──────────────┘  └────────────┘   │
│     ↓            ↓               ↓                 ↓             │
│   ┌────────────────────────────────────────────────────────┐   │
│   │              POSTGRES (Primary)                        │   │
│   │  - 1 StatefulSet replica                              │   │
│   │  - 20GB PersistentVolume                              │   │
│   │  - Connection pool: 10-20 async                       │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                   │
│   ┌────────────────────────────────────────────────────────┐   │
│   │                    REDIS (Cache)                       │   │
│   │  - 1 StatefulSet replica                              │   │
│   │  - TTL-based eviction policy                          │   │
│   │  - Used by: User, Market Data, Analytics             │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                   │
│   ┌────────────────────────────────────────────────────────┐   │
│   │              KAFKA (3 broker cluster)                  │   │
│   │  - Zookeeper 1 replica for coordination               │   │
│   │  - 50GB PersistentVolume per broker                   │   │
│   │  - Topics: price_updates, sentiment_scores, portfolio │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Kubernetes Cluster**: 1.20+ (tested on 1.28)
- **Storage**: 140GB total (20GB Postgres + 50GB Kafka×3)
- **Compute**: 
  - Minimum: 3 nodes (2 CPU, 4GB RAM each)
  - Recommended: 5 nodes (4 CPU, 8GB RAM each)
- **Tools installed**:
  ```bash
  kubectl (v1.28+)
  helm (v3.10+) - for future package management
  ```

## Deployment Steps

### Step 1: Create Kubernetes Cluster

#### Using Minikube (Development)
```bash
minikube start --cpus=4 --memory=8192 --disk-size=100gb --addons=ingress
minikube addons enable metrics-server
```

#### Using AWS EKS (Production)
```bash
eksctl create cluster --name crypto-analytics \
  --region us-east-1 \
  --node-type t3.xlarge \
  --nodes 5 \
  --managed
```

#### Using GKE (Production)
```bash
gcloud container clusters create crypto-analytics \
  --zone us-central1-a \
  --num-nodes 5 \
  --machine-type n1-standard-4 \
  --disk-size 100 \
  --disk-type pd-standard
```

### Step 2: Install Required Components

#### Install Ingress Controller (if not included)
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx
```

#### Install Cert-Manager for TLS (Optional but recommended)
```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true
```

#### Create Certificate Issuer for Let's Encrypt
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@crypto-analytics.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Step 3: Build and Push Docker Images

Before deploying, build and push Docker images to your registry:

```bash
# Set registry
REGISTRY=your-docker-registry

# Build all services
cd /home/duc/analytics
docker-compose build

# Tag and push
docker tag crypto-user-service:latest $REGISTRY/crypto-user-service:latest
docker tag crypto-api-gateway:latest $REGISTRY/crypto-api-gateway:latest
docker tag crypto-market-data-service:latest $REGISTRY/crypto-market-data-service:latest
docker tag crypto-analytics-service:latest $REGISTRY/crypto-analytics-service:latest
docker tag crypto-sentiment-service:latest $REGISTRY/crypto-sentiment-service:latest
docker tag crypto-portfolio-service:latest $REGISTRY/crypto-portfolio-service:latest

docker push $REGISTRY/crypto-user-service:latest
docker push $REGISTRY/crypto-api-gateway:latest
docker push $REGISTRY/crypto-market-data-service:latest
docker push $REGISTRY/crypto-analytics-service:latest
docker push $REGISTRY/crypto-sentiment-service:latest
docker push $REGISTRY/crypto-portfolio-service:latest

# Update imagePullSecrets in manifests if using private registry
kubectl create secret docker-registry regcred \
  --docker-server=$REGISTRY \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email> \
  -n crypto
```

### Step 4: Deploy Infrastructure

```bash
# Apply manifests in order
kubectl apply -f k8s/01-infrastructure.yaml
kubectl apply -f k8s/02-services.yaml
kubectl apply -f k8s/03-ingress.yaml
kubectl apply -f k8s/04-kafka.yaml
kubectl apply -f k8s/05-portfolio-monitoring.yaml

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod --all -n crypto --timeout=300s
```

### Step 5: Initialize Database

```bash
# Port-forward to PostgreSQL
kubectl port-forward -n crypto svc/postgres-primary 5432:5432 &

# Run migrations
psql postgresql://crypto_user:crypto_password@localhost:5432/crypto_db \
  -f migrations/001_initial_schema.sql

# Verify tables created
psql postgresql://crypto_user:crypto_password@localhost:5432/crypto_db \
  -c "\dt"
```

### Step 6: Create Kafka Topics

```bash
# Port-forward to Kafka
kubectl port-forward -n crypto svc/kafka-bootstrap 9092:9092 &

# Create topics from any pod
kubectl exec -it -n crypto kafka-0 -- bash -c '
kafka-topics.sh --create \
  --topic price_updates \
  --partitions 3 \
  --replication-factor 3 \
  --bootstrap-server kafka-0.kafka:9092 \
  --if-not-exists

kafka-topics.sh --create \
  --topic sentiment_scores \
  --partitions 3 \
  --replication-factor 3 \
  --bootstrap-server kafka-0.kafka:9092 \
  --if-not-exists

kafka-topics.sh --create \
  --topic portfolio_updates \
  --partitions 3 \
  --replication-factor 3 \
  --bootstrap-server kafka-0.kafka:9092 \
  --if-not-exists
'

# Verify topics
kubectl exec -it -n crypto kafka-0 -- \
  kafka-topics.sh --list --bootstrap-server kafka-0.kafka:9092
```

### Step 7: Verify Deployment

```bash
# Check all resources in crypto namespace
kubectl get all -n crypto

# Check pod status
kubectl get pods -n crypto

# Check services
kubectl get svc -n crypto

# Check ingress
kubectl get ingress -n crypto

# View logs from a specific service
kubectl logs -n crypto -l app=api-gateway --tail=100 -f

# Describe deployment for debugging
kubectl describe deployment api-gateway -n crypto
```

### Step 8: Access the Application

#### Minikube
```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Add to /etc/hosts
echo "$MINIKUBE_IP api.crypto-analytics.com" | sudo tee -a /etc/hosts

# Port-forward API Gateway
kubectl port-forward -n crypto svc/api-gateway 8000:8000

# Access at http://localhost:8000
```

#### AWS EKS / GKE
```bash
# Get external IP/DNS
kubectl get svc api-gateway -n crypto

# Access via LoadBalancer endpoint or Ingress domain
# Wait for DNS propagation if using custom domain
```

## Scaling Configuration

### Current HPA Settings

| Service | Min | Max | CPU % | Memory % |
|---------|-----|-----|-------|----------|
| API Gateway | 3 | 10 | 70% | 80% |
| Analytics | 3 | 10 | 75% | 80% |
| Market Data | 2 | 8 | 75% | N/A |

### Manual Scaling

```bash
# Scale to specific replicas
kubectl scale deployment api-gateway -n crypto --replicas=5

# Edit HPA limits
kubectl edit hpa api-gateway-hpa -n crypto

# View current scaling metrics
kubectl top nodes
kubectl top pods -n crypto
```

## Monitoring and Observability

### Health Checks

All services expose `/health` endpoints:
```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://api-gateway:8000/health
```

### Pod Logs

```bash
# View logs from specific pod
kubectl logs -n crypto api-gateway-abc123 -f

# View logs from all pods of a service
kubectl logs -n crypto -l app=analytics-service --tail=50

# View logs with timestamp
kubectl logs -n crypto api-gateway-abc123 --timestamps=true
```

### Resource Usage

```bash
# Check CPU/Memory usage per pod
kubectl top pods -n crypto

# Check CPU/Memory usage per node
kubectl top nodes

# Set resource requests/limits (already in manifests)
kubectl set resources deployment api-gateway -n crypto \
  --requests=cpu=500m,memory=512Mi \
  --limits=cpu=1000m,memory=1Gi
```

## Troubleshooting

### Pod CrashLoopBackOff

```bash
# Check logs
kubectl logs -n crypto <pod-name> --previous

# Describe pod for events
kubectl describe pod -n crypto <pod-name>

# Check resource availability
kubectl top pods -n crypto
kubectl top nodes

# Check liveness probe configuration
kubectl get pod -n crypto <pod-name> -o yaml | grep -A 10 livenessProbe
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
kubectl run -it --rm psql --image=postgres:15 --restart=Never -- \
  psql -h postgres-primary.crypto -U crypto_user -d crypto_db

# Check password in secret
kubectl get secret -n crypto crypto-secrets -o yaml

# Verify DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup postgres-primary.crypto
```

### Kafka Issues

```bash
# Check Zookeeper status
kubectl exec -it -n crypto zookeeper-0 -- \
  zkServer.sh status

# Check Kafka broker logs
kubectl logs -n crypto kafka-0

# Check Kafka connectivity
kubectl exec -it -n crypto kafka-0 -- \
  kafka-broker-api-versions.sh --bootstrap-server kafka-0.kafka:9092

# List topics
kubectl exec -it -n crypto kafka-0 -- \
  kafka-topics.sh --list --bootstrap-server kafka-0.kafka:9092
```

### Service-to-Service Communication

```bash
# Test service discovery (from within cluster)
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://api-gateway:8000/health

# Check DNS records
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup api-gateway.crypto
```

## Maintenance Operations

### Database Backup

```bash
# Create PostgreSQL backup
kubectl exec -n crypto postgres-0 -- \
  pg_dump -U crypto_user crypto_db | gzip > backup.sql.gz

# Restore from backup
gunzip -c backup.sql.gz | \
  kubectl exec -i -n crypto postgres-0 -- \
  psql -U crypto_user crypto_db
```

### Rolling Updates

```bash
# Update image for a service
kubectl set image deployment/api-gateway \
  api-gateway=my-registry/crypto-api-gateway:v2 \
  -n crypto

# Watch rollout progress
kubectl rollout status deployment/api-gateway -n crypto

# Rollback if issues
kubectl rollout undo deployment/api-gateway -n crypto
```

### Pod Eviction and Disruption

```bash
# Drain node for maintenance (respects PDB)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Uncordon node after maintenance
kubectl uncordon <node-name>

# Check Pod Disruption Budgets
kubectl get pdb -n crypto
```

## Performance Optimization

### Connection Pooling

- **PostgreSQL**: asyncpg driver with pool_size=10, max_overflow=20
- **Redis**: Connection pooling via aioredis

### Caching Strategy

| Resource | TTL | Key Pattern |
|----------|-----|-------------|
| Current Price | 5s | `price:{coin_id}` |
| Analytics Metric | 5min | `analytics:{metric}:{coin_id}:{period}` |
| Sentiment Score | 1h | `sentiment:{coin_id}` |
| User Profile | 15min | `user:{user_id}` |

### Resource Requests/Limits

Already configured in manifests based on actual workloads:
- **Metadata Services**: 500m/512Mi (request/limit)
- **Analytics Service**: 2000m/2Gi (compute-intensive)
- **Market Data Service**: 1000m/1Gi (I/O heavy)

## Network Policies

The cluster includes a NetworkPolicy restricting traffic to:
1. Internal pod-to-pod communication within `crypto` namespace
2. DNS egress to kube-system (port 53)
3. HTTPS egress for external APIs (port 443)

To modify network policies:
```bash
kubectl edit networkpolicy crypto-network-policy -n crypto
```

## Production Checklist

- [ ] All images pushed to production registry with digest-based tags
- [ ] Secrets using actual values (JWT_SECRET_KEY, DB_PASSWORD, API keys)
- [ ] TLS certificates installed for Ingress
- [ ] PersistentVolumes backed by production storage (EBS, GCE PD, etc.)
- [ ] Monitoring and alerting configured (Prometheus, Grafana, AlertManager)
- [ ] Log aggregation configured (Loki, ELK, Datadog, etc.)
- [ ] Resource quotas set per namespace
- [ ] Network policies enforced
- [ ] RBAC rules configured for service accounts
- [ ] Pod Security Policies or Standards enforced
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Backup strategy tested

## Cleanup

To remove all resources:

```bash
# Delete all manifests
kubectl delete -f k8s/

# Delete namespace (all resources within deleted)
kubectl delete namespace crypto

# For EKS/GKE, also delete cluster
eksctl delete cluster --name crypto-analytics
gcloud container clusters delete crypto-analytics
```
