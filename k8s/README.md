# Kubernetes Configuration Files

This directory contains all Kubernetes manifests for deploying the Crypto Analytics Platform to a production Kubernetes cluster.

## File Structure

```
k8s/
├── 01-infrastructure.yaml      # Namespace, ConfigMap, Secrets, PostgreSQL, Redis
├── 02-services.yaml            # User, API Gateway, Market Data, Analytics, Sentiment Services
├── 03-ingress.yaml             # Ingress rules, HPA autoscaling, Network policies
├── 04-kafka.yaml               # Zookeeper, Kafka StatefulSets with 3 broker cluster
├── 05-portfolio-monitoring.yaml # Portfolio Service, ServiceMonitor, Pod Disruption Budgets
├── 06-monitoring.yaml          # Prometheus, Alertmanager with alert rules
└── 07-grafana.yaml             # Grafana deployment with datasources and dashboards
```

## Quick Start

### Prerequisites
```bash
# Kubernetes 1.20+
kubectl version --client

# kubectl access
kubectl cluster-info
```

### Deploy All Services (Recommended Order)

```bash
# 1. Create infrastructure first (namespace, storage, database, cache)
kubectl apply -f k8s/01-infrastructure.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n crypto --timeout=120s

# 2. Deploy Kafka message queue
kubectl apply -f k8s/04-kafka.yaml
kubectl wait --for=condition=ready pod -l app=kafka -n crypto --timeout=180s

# 3. Deploy application services
kubectl apply -f k8s/02-services.yaml
kubectl wait --for=condition=ready pod -l app in (user-service,api-gateway,market-data-service,analytics-service,sentiment-service) -n crypto --timeout=120s

# 4. Configure routing and networking
kubectl apply -f k8s/03-ingress.yaml

# 5. Add portfolio service and PDBs
kubectl apply -f k8s/05-portfolio-monitoring.yaml

# 6. Deploy monitoring stack
kubectl create namespace monitoring
kubectl apply -f k8s/06-monitoring.yaml
kubectl apply -f k8s/07-grafana.yaml

# 7. Verify all pods are running
kubectl get pods -n crypto
kubectl get pods -n monitoring
```

### Initialize Database

```bash
# Port forward to PostgreSQL
kubectl port-forward -n crypto svc/postgres-primary 5432:5432 &

# Run migration SQL
psql postgresql://crypto_user:crypto_password@localhost:5432/crypto_db < migrations/001_initial_schema.sql

# Verify tables
psql postgresql://crypto_user:crypto_password@localhost:5432/crypto_db -c "\dt"
```

### Create Kafka Topics

```bash
# Port forward to Kafka
kubectl port-forward -n crypto svc/kafka-bootstrap 9092:9092 &

# Create topics
kubectl exec -it -n crypto kafka-0 -- kafka-topics.sh \
  --create --topic price_updates --partitions 3 --replication-factor 3 \
  --bootstrap-server kafka-0.kafka:9092 --if-not-exists

kubectl exec -it -n crypto kafka-0 -- kafka-topics.sh \
  --create --topic sentiment_scores --partitions 3 --replication-factor 3 \
  --bootstrap-server kafka-0.kafka:9092 --if-not-exists

kubectl exec -it -n crypto kafka-0 -- kafka-topics.sh \
  --create --topic portfolio_updates --partitions 3 --replication-factor 3 \
  --bootstrap-server kafka-0.kafka:9092 --if-not-exists
```

## Manifest Details

### 01-infrastructure.yaml
**Components:**
- **Namespace**: `crypto` - isolated environment for all application pods
- **ConfigMap** (`crypto-config`): Environment variables shared by all services
  - `KAFKA_BROKERS`, `DATABASE_URL`, `REDIS_URL`, `JWT_ALGORITHM`, etc.
- **Secrets** (`crypto-secrets`): Sensitive data
  - `JWT_SECRET_KEY`, `DB_PASSWORD`, `NEWSAPI_KEY`
- **PostgreSQL StatefulSet**:
  - 1 replica, persistent 20GB storage
  - Health checks with pg_isready
  - Connection pooling via application code
- **Redis StatefulSet**:
  - 1 replica, RDB persistence with AOF
  - Health checks with redis-cli ping

**Access:**
```bash
# PostgreSQL
kubectl port-forward -n crypto svc/postgres-primary 5432:5432

# Redis
kubectl port-forward -n crypto svc/redis 6379:6379
```

### 02-services.yaml
**Deployments:**
- **User Service**: 2 replicas, 8001/tcp
- **API Gateway**: 3 replicas, LoadBalancer on port 80/443
- **Market Data Service**: 2 replicas, 8002/tcp (connects to Binance/Coinbase)
- **Analytics Service**: 3 replicas, 8003/tcp (compute-intensive)
- **Sentiment Service**: 2 replicas, 8004/tcp

**Resource Configuration:**
- Small services (User, Sentiment): 500m/512Mi → 1000m/1Gi
- Market Data (I/O heavy): 1000m/1Gi → 2000m/2Gi
- Analytics (CPU-intensive): 2000m/2Gi → 4000m/4Gi

**Probe Configuration:**
- Liveness: 30s initial delay, 10s period → restart unhealthy pods
- Readiness: 10s initial delay, 5s period → remove from load balancer

### 03-ingress.yaml
**Features:**
- **Ingress Controller**: nginx (requires ingress-nginx installation)
- **TLS**: Auto-managed by cert-manager (requires cert-manager installation)
- **Domain**: `api.crypto-analytics.com`
- **HPA for API Gateway**:
  - Min replicas: 3, Max replicas: 10
  - Scale up: CPU > 70% or Memory > 80%
  - Scale down: CPU < 70% and Memory < 80%
- **HPA for Analytics Service**:
  - Min replicas: 3, Max replicas: 10
  - Scale up: CPU > 75% or Memory > 80%
- **Network Policy**:
  - Restricts traffic to crypto namespace
  - Allows egress to kube-system (DNS) and external HTTPS

### 04-kafka.yaml
**Kafka Cluster:**
- 3 broker StatefulSet with headless service
- 1 Zookeeper replica for coordination
- 50GB persistent storage per broker
- Replication factor: 3 across brokers
- Auto-created topics: price_updates, sentiment_scores, portfolio_updates
- Log retention: 30 days (720 hours)
- Partition count: 3 per topic

**Services:**
- `kafka-0.kafka`, `kafka-1.kafka`, `kafka-2.kafka` (DNS names in cluster)
- `kafka-bootstrap`: LoadBalancer for external Kafka consumers
- `zookeeper-0.zookeeper`: Zookeeper coordination

**Monitoring:**
```bash
# Check broker status
kubectl exec -it -n crypto kafka-0 -- \
  kafka-broker-api-versions.sh --bootstrap-server kafka-0.kafka:9092

# Monitor topics
kubectl exec -it -n crypto kafka-0 -- \
  kafka-console-consumer.sh --bootstrap-server kafka-0.kafka:9092 \
  --topic price_updates --from-beginning --max-messages 10
```

### 05-portfolio-monitoring.yaml
**Components:**
- **Portfolio Service Deployment**: 2 replicas, 8005/tcp
- **ServiceMonitor**: Enables Prometheus scraping (if using kube-prometheus-stack)
- **Pod Disruption Budgets**:
  - API Gateway: minAvailable=1 (at least 1 pod must be running during disruption)
  - Analytics Service: minAvailable=2 (at least 2 pods during disruption)

### 06-monitoring.yaml
**Prometheus:**
- 2 replicas for redundancy
- Scrapes every 15 seconds with 30-second evaluation interval
- 30-day data retention
- Discovers services via Kubernetes API
- Alert rules for: CPU/memory, service availability, HTTP errors, database, Kafka, performance

**Alert Rules:**
- **Critical**: ServiceDown (2min), CriticalCPU (95%), OutOfMemory (95%), KafkaBrokerDown
- **Warning**: HighCPU (80%), HighMemory (90%), PodRestart, HighErrorRate, Kafka under-replication

**Alertmanager:**
- 3 replicas (distributed consensus)
- Routes alerts to Slack channels by severity
- Critical alerts: 5-minute repeat (high visibility)
- Warning alerts: 12-hour repeat (less intrusive)

**Setup:**
```bash
# Update Slack webhook URL in alertmanager config
kubectl edit configmap alertmanager-config -n monitoring
# Replace: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Verify alerts
kubectl logs -n monitoring alertmanager-0 -f
```

### 07-grafana.yaml
**Grafana:**
- 1 replica (stateless, can scale horizontally)
- Default admin password: `admin` (change in production)
- Datasource: Prometheus (http://prometheus:9090)
- Pre-configured dashboards:
  - CPU/Memory usage per pod
  - Service status (up/down)
  - HTTP request rates

**Accessing Grafana:**

```bash
# Port forward
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Open browser: http://localhost:3000
# Login: admin / admin

# Or via Ingress (if configured): https://grafana.crypto-analytics.com
```

**Dashboard Customization:**
```bash
# Add new dashboard via Grafana UI or
# Import JSON via ConfigMap and restart Grafana
kubectl edit configmap grafana-dashboards -n monitoring
kubectl rollout restart deployment grafana -n monitoring
```

## Common Operations

### Scale a Service
```bash
# Manual scaling
kubectl scale deployment api-gateway -n crypto --replicas=5

# Check HPA status
kubectl get hpa -n crypto
kubectl describe hpa api-gateway-hpa -n crypto

# Edit HPA limits
kubectl edit hpa api-gateway-hpa -n crypto
```

### View Logs
```bash
# Single pod
kubectl logs -n crypto api-gateway-abc123 -f

# All pods of a service
kubectl logs -n crypto -l app=analytics-service --tail=100 -f

# Previous crashed pod
kubectl logs -n crypto api-gateway-abc123 --previous
```

### Port Forwarding
```bash
# API Gateway
kubectl port-forward -n crypto svc/api-gateway 8000:8000

# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# PostgreSQL
kubectl port-forward -n crypto svc/postgres-primary 5432:5432

# Kafka bootstrap
kubectl port-forward -n crypto svc/kafka-bootstrap 9092:9092
```

### Execute Commands in Pods
```bash
# Run interactive shell
kubectl exec -it -n crypto api-gateway-abc123 -- /bin/sh

# Run single command
kubectl exec -n crypto api-gateway-abc123 -- curl http://localhost:8000/health

# Run in service (random pod)
kubectl exec -it -n crypto -l app=user-service -- psql -h postgres-primary -U crypto_user
```

### Debug Network Issues
```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup api-gateway.crypto

# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://api-gateway:8000/health

# Test external connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
```

### Update Secret
```bash
# View current secret
kubectl get secret -n crypto crypto-secrets -o yaml

# Edit secret (base64 encoded)
kubectl edit secret -n crypto crypto-secrets

# Or delete and recreate
kubectl delete secret -n crypto crypto-secrets
kubectl create secret generic crypto-secrets -n crypto \
  --from-literal=JWT_SECRET_KEY=new-secret \
  --from-literal=DB_PASSWORD=new-password \
  --from-literal=NEWSAPI_KEY=new-key
```

### Rolling Update
```bash
# Update image
kubectl set image deployment/api-gateway \
  api-gateway=my-registry/crypto-api-gateway:v2 -n crypto

# Watch rollout
kubectl rollout status deployment/api-gateway -n crypto

# Rollback if needed
kubectl rollout undo deployment/api-gateway -n crypto

# Check rollout history
kubectl rollout history deployment/api-gateway -n crypto
```

### Database Backup/Restore
```bash
# Backup
kubectl exec -n crypto postgres-0 -- \
  pg_dump -U crypto_user crypto_db | gzip > backup.sql.gz

# Restore
gunzip -c backup.sql.gz | \
  kubectl exec -i -n crypto postgres-0 -- \
  psql -U crypto_user crypto_db
```

## Troubleshooting

### Pod CrashLoopBackOff
```bash
kubectl describe pod -n crypto <pod-name>
kubectl logs -n crypto <pod-name> --previous
```

### Service Unavailable
```bash
kubectl get svc -n crypto
kubectl describe svc -n crypto <service-name>
kubectl get endpoints -n crypto
```

### Ingress Not Working
```bash
kubectl get ingress -n crypto
kubectl describe ingress -n crypto crypto-ingress
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

### Kafka Consumer Lag
```bash
kubectl exec -it -n crypto kafka-0 -- \
  kafka-consumer-groups.sh --bootstrap-server kafka-0.kafka:9092 \
  --group crypto-analytics --describe
```

### Database Connection Pool Exhausted
```bash
# Check active connections
kubectl port-forward -n crypto svc/postgres-primary 5432:5432 &
psql postgresql://crypto_user:crypto_password@localhost:5432/crypto_db \
  -c "SELECT count(*) FROM pg_stat_activity;"
```

## Production Checklist

- [ ] All images use specific version tags (no `latest`)
- [ ] Secrets are encrypted at rest (enable encryption in etcd)
- [ ] StorageClass configured with proper replication and snapshots
- [ ] Network policies enforced and tested
- [ ] RBAC rules configured for service accounts
- [ ] Resource quotas set per namespace
- [ ] Pod Security Policy or Pod Security Standards enforced
- [ ] Monitoring and alerting configured and tested
- [ ] Log aggregation (ELK, Loki, Splunk) configured
- [ ] Backup strategy tested and verified
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security scanning (Trivy, Snyk) integrated into CI/CD
- [ ] Ingress/TLS certificates renewed automatically (cert-manager)
- [ ] Node autoscaling configured for cloud platforms
- [ ] Pod disruption budgets reviewed
- [ ] High availability for stateful services verified

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [Grafana Deployment](https://grafana.com/grafana/download)
- [Kafka on Kubernetes](https://github.com/confluentinc/cp-helm-charts)
