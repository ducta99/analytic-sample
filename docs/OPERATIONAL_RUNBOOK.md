# Operational Runbook

**Version**: 1.0 | **Last Updated**: October 25, 2025

This runbook provides operational procedures for running and maintaining the Cryptocurrency Analytics Dashboard in production.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Incident Response](#incident-response)
3. [Common Alerts and Solutions](#common-alerts-and-solutions)
4. [Scaling Procedures](#scaling-procedures)
5. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
6. [Performance Tuning](#performance-tuning)
7. [Security Operations](#security-operations)
8. [Maintenance Windows](#maintenance-windows)

---

## Daily Operations

### Morning Health Check (8:00 AM)

```bash
#!/bin/bash
# health_check.sh

set -e

echo "=== Daily Health Check ==="
echo "[$(date)] Starting health check..."

# Check Kubernetes cluster
kubectl cluster-info
echo "✓ Kubernetes cluster healthy"

# Check pod status
UNHEALTHY=$(kubectl get pods -n crypto --field-selector=status.phase!=Running,status.phase!=Succeeded)
if [ -z "$UNHEALTHY" ]; then
    echo "✓ All pods running"
else
    echo "⚠ Unhealthy pods detected:"
    echo "$UNHEALTHY"
fi

# Check API Gateway
if curl -f http://api-gateway.crypto.svc:8000/api/health > /dev/null; then
    echo "✓ API Gateway healthy"
else
    echo "✗ API Gateway unhealthy - ALERT!"
fi

# Check database
PSQL_RESULT=$(kubectl exec -it postgres-0 -n crypto -- psql -U crypto_user -d crypto_db -c "SELECT 1" 2>/dev/null || echo "FAIL")
if [ "$PSQL_RESULT" != "FAIL" ]; then
    echo "✓ PostgreSQL healthy"
else
    echo "✗ PostgreSQL unhealthy - ALERT!"
fi

# Check Redis
if kubectl exec redis-0 -n crypto -- redis-cli ping | grep -q PONG; then
    echo "✓ Redis healthy"
else
    echo "✗ Redis unhealthy - ALERT!"
fi

# Check Kafka
KAFKA_STATUS=$(kubectl exec kafka-0 -n crypto -- kafka-broker-api-versions.sh --bootstrap-server localhost:9092 2>/dev/null || echo "FAIL")
if [ "$KAFKA_STATUS" != "FAIL" ]; then
    echo "✓ Kafka cluster healthy"
else
    echo "✗ Kafka unhealthy - ALERT!"
fi

# Check disk space
DISK_USAGE=$(kubectl exec postgres-0 -n crypto -- df -h /var/lib/postgresql | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "✓ Disk usage: ${DISK_USAGE}%"
else
    echo "⚠ High disk usage: ${DISK_USAGE}% - Consider cleanup"
fi

# Check Prometheus metrics
PROMETHEUS_TARGETS=$(curl -s http://prometheus.crypto.svc:9090/api/v1/targets | jq '.data.activeTargets | length')
echo "✓ Prometheus tracking $PROMETHEUS_TARGETS targets"

echo "[$(date)] Health check complete"
```

Run daily:

```bash
0 8 * * * /opt/scripts/health_check.sh | mail -s "Daily Health Check" ops@example.com
```

### Monitoring Dashboard Check (Hourly)

1. Access Grafana: https://grafana.cryptoanalytics.com
2. Check dashboards:
   - **API Gateway Dashboard**: Response times < 200ms (p95)
   - **Infrastructure Dashboard**: Node CPU/Memory < 80%
   - **Business Metrics**: Prices updated, sentiment processed
   - **Error Rate**: < 0.5%

### Log Review

```bash
# Check for errors in past hour
kubectl logs --all-containers=true \
  --since=1h \
  -n crypto \
  --timestamps=true | grep -i error | head -20

# Monitor API Gateway logs in real-time
kubectl logs -f deployment/api-gateway -n crypto

# Search for specific error pattern
kubectl logs --tail=1000 -n crypto -l app=api-gateway | grep "500\|CRITICAL"
```

---

## Incident Response

### Incident Severity Levels

| Level | Impact | Response Time | Pages |
|-------|--------|----------------|-------|
| P1 | Production down | 15 minutes | Everyone |
| P2 | Major feature broken | 30 minutes | On-call team |
| P3 | Minor issue | 2 hours | Support team |
| P4 | Enhancement request | Next sprint | Backlog |

### Incident Response Process

#### Step 1: Detection

Alerts from Prometheus trigger Slack/PagerDuty notifications.

#### Step 2: Acknowledge

```bash
# For PagerDuty
pagerduty-cli incident acknowledge <incident-id>

# For Slack
React with 👀 to incident notification
```

#### Step 3: Assess Severity

- Is production API down?
- How many users affected?
- Data loss risk?
- Revenue impact?

#### Step 4: Initiate Response

```bash
# P1: Start war room
# Conference: https://meet.example.com/incident-<timestamp>
# Create incident ticket: https://jira.example.com

# Notify stakeholders
slack-message "🔴 P1 INCIDENT: $(incident_summary)" #incidents
```

#### Step 5: Diagnose

```bash
# Collect logs
kubectl logs -n crypto deployment/api-gateway --tail=500 > /tmp/api-gateway.log

# Check metrics
curl http://prometheus:9090/api/v1/query?query=up{job="api-gateway"}

# Check resource usage
kubectl top nodes -n crypto
kubectl top pods -n crypto

# Describe failing pods
kubectl describe pod <pod-name> -n crypto
```

#### Step 6: Implement Fix

See specific alert procedures below.

#### Step 7: Communicate

- Update incident ticket every 15 minutes
- Notify #incidents channel of progress
- Send RCA within 24 hours

---

## Common Alerts and Solutions

### Alert: API Gateway - High Error Rate (>1%)

**Symptom**: Error rate spike, 500 errors in logs

**Diagnosis**:
```bash
# Check logs for errors
kubectl logs -n crypto deployment/api-gateway | grep ERROR

# Check downstream services
curl http://user-service:8001/health
curl http://market-data-service:8002/health
curl http://analytics-service:8003/health
curl http://sentiment-service:8004/health

# Check database connection pool
kubectl exec -it postgres-0 -n crypto -- \
  psql -U crypto_user -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

**Solutions**:

1. **Database Connection Pool Exhausted**
   ```bash
   # Increase connection pool
   kubectl edit configmap app-config -n crypto
   # Set DATABASE_POOL_SIZE=30, DATABASE_MAX_OVERFLOW=50
   
   # Restart services
   kubectl rollout restart deployment/api-gateway -n crypto
   kubectl rollout restart deployment/user-service -n crypto
   ```

2. **Downstream Service Unavailable**
   ```bash
   # Check pod status
   kubectl get pods -n crypto | grep -E "user-service|analytics|sentiment"
   
   # Restart service if needed
   kubectl rollout restart deployment/user-service -n crypto
   
   # Check recent logs
   kubectl logs -n crypto deployment/user-service --tail=100
   ```

3. **Memory Leak**
   ```bash
   # Check memory usage
   kubectl top pods -n crypto --sort-by=memory
   
   # If service using >1GB:
   kubectl delete pod <pod-name> -n crypto  # Trigger restart
   
   # Monitor memory trend
   kubectl logs -n crypto deployment/api-gateway | grep "memory usage"
   ```

### Alert: Database - Connection Pool Exhausted

**Symptom**: "too many connections" errors

**Diagnosis**:
```bash
# Check active connections
kubectl exec -it postgres-0 -n crypto -- \
  psql -U crypto_user -d crypto_db -c \
  "SELECT pid, usename, application_name, state FROM pg_stat_activity;"

# Check long-running queries
kubectl exec -it postgres-0 -n crypto -- \
  psql -U crypto_user -d crypto_db -c \
  "SELECT pid, now() - pg_stat_activity.query_start as duration, query FROM pg_stat_activity WHERE query != '<IDLE>';"
```

**Solutions**:

1. **Kill Idle Connections**
   ```bash
   # Terminate idle connections older than 30 minutes
   kubectl exec -it postgres-0 -n crypto -- psql -U crypto_user -d crypto_db <<EOF
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE state='idle' 
   AND now() - query_start > interval '30 minutes';
   EOF
   ```

2. **Increase Connection Limits**
   ```bash
   kubectl edit statefulset postgres -n crypto
   # Increase max_connections in postgresql.conf
   # Default: 100, Recommended: 200-300
   ```

3. **Optimize Connection Pool**
   ```python
   # In shared/db_pool.py
   DATABASE_POOL_SIZE = 30  # Default connections
   DATABASE_MAX_OVERFLOW = 50  # Max additional
   DATABASE_POOL_TIMEOUT = 10  # Wait timeout
   DATABASE_POOL_RECYCLE = 3600  # Recycle after 1 hour
   ```

### Alert: Redis - Memory Usage High (>80%)

**Symptom**: Redis slow, potential evictions

**Diagnosis**:
```bash
# Check Redis memory
kubectl exec redis-0 -n crypto -- redis-cli INFO memory

# Check top keys
kubectl exec redis-0 -n crypto -- \
  redis-cli --bigkeys | head -20

# Check key sizes
kubectl exec redis-0 -n crypto -- \
  redis-cli --memkeys | head -20
```

**Solutions**:

1. **Clear Old Cache**
   ```bash
   # Clear all cache (careful!)
   kubectl exec redis-0 -n crypto -- redis-cli FLUSHALL
   
   # Or clear specific pattern
   kubectl exec redis-0 -n crypto -- redis-cli EVAL \
     "return redis.call('del', unpack(redis.call('keys', ARGV[1])))" \
     0 "price:*:old"
   ```

2. **Increase Memory Limit**
   ```bash
   # Edit Redis StatefulSet
   kubectl edit statefulset redis -n crypto
   # Increase memory: 2Gi -> 4Gi
   
   # Or update Redis config
   kubectl exec redis-0 -n crypto -- \
     redis-cli CONFIG SET maxmemory 4gb
   ```

3. **Enable Eviction Policy**
   ```bash
   # Set eviction policy to LRU (Least Recently Used)
   kubectl exec redis-0 -n crypto -- \
     redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

### Alert: Kafka - Consumer Lag High (>10k messages)

**Symptom**: Delayed analytics processing, sentiment updates

**Diagnosis**:
```bash
# Check consumer lag
kubectl exec kafka-0 -n crypto -- \
  kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group analytics-service \
  --describe

# Check topic lag
kubectl exec kafka-0 -n crypto -- \
  kafka-run-class.sh kafka.tools.JmxTool \
  --object-name kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*
```

**Solutions**:

1. **Scale Analytics Service**
   ```bash
   # Check current replicas
   kubectl get deployment analytics -n crypto

   # Scale to more replicas
   kubectl scale deployment analytics --replicas=5 -n crypto

   # Monitor lag
   watch -n 5 'kubectl exec kafka-0 -n crypto -- \
     kafka-consumer-groups.sh \
     --bootstrap-server localhost:9092 \
     --group analytics-service \
     --describe'
   ```

2. **Check Service Logs**
   ```bash
   kubectl logs -f deployment/analytics -n crypto | grep -E "ERROR|lag|lag_offset"
   ```

3. **Increase Kafka Partitions** (careful - may require rebalance)
   ```bash
   kubectl exec kafka-0 -n crypto -- \
     kafka-topics.sh \
     --bootstrap-server localhost:9092 \
     --topic price_updates \
     --alter \
     --partitions 24
   ```

### Alert: Sentiment Service - NLP Model Loading Failure

**Symptom**: Pod crashes, restarts continuously

**Diagnosis**:
```bash
# Check pod logs
kubectl logs deployment/sentiment -n crypto --tail=50

# Typical error: CUDA out of memory or model download failure
```

**Solutions**:

1. **Increase Memory Allocation**
   ```bash
   kubectl edit deployment sentiment -n crypto
   # Increase resources.requests.memory: 2Gi -> 4Gi
   # Increase resources.limits.memory: 4Gi -> 8Gi
   ```

2. **Disable CUDA (use CPU)**
   ```bash
   kubectl set env deployment/sentiment \
     TORCH_DEVICE=cpu \
     -n crypto
   ```

3. **Use Smaller Model**
   ```bash
   kubectl set env deployment/sentiment \
     HUGGINGFACE_MODEL=distilbert-base-uncased \
     -n crypto
   ```

---

## Scaling Procedures

### Horizontal Pod Autoscaling

Check current HPA:

```bash
kubectl get hpa -n crypto
```

### Manual Scaling for Peak Hours

```bash
# Morning surge (8 AM - 10 AM)
kubectl scale deployment api-gateway --replicas=10 -n crypto
kubectl scale deployment analytics --replicas=8 -n crypto
kubectl scale deployment sentiment --replicas=5 -n crypto

# Check scaling progress
kubectl get deployment -n crypto --watch

# Return to normal after peak
kubectl scale deployment api-gateway --replicas=3 -n crypto
kubectl scale deployment analytics --replicas=3 -n crypto
kubectl scale deployment sentiment --replicas=2 -n crypto
```

### Database Connection Pool Scaling

```bash
# Monitor connection usage
kubectl exec -it postgres-0 -n crypto -- \
  watch -n 2 'psql -U crypto_user -d crypto_db \
  -c "SELECT count(*) as connections FROM pg_stat_activity;"'

# Adjust pool size if needed
kubectl edit configmap app-config -n crypto
# DATABASE_POOL_SIZE based on: (CPU_CORES * 2) + 4
# Example: 4 cores -> pool size 12
```

---

## Backup and Disaster Recovery

### Database Backups

```bash
#!/bin/bash
# daily_backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/postgresql

# Create backup
kubectl exec postgres-0 -n crypto -- \
  pg_dump -U crypto_user -d crypto_db | \
  gzip > $BACKUP_DIR/crypto_db_$TIMESTAMP.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/crypto_db_$TIMESTAMP.sql.gz \
  s3://backups/crypto-analytics/

echo "Backup completed: $TIMESTAMP"
```

Schedule daily:

```bash
0 2 * * * /opt/scripts/daily_backup.sh
```

### Database Recovery

```bash
# Restore from backup
kubectl exec postgres-0 -n crypto -- \
  gunzip -c /backups/crypto_db_20251025_020000.sql.gz | \
  psql -U crypto_user -d crypto_db

# Verify restore
kubectl exec postgres-0 -n crypto -- \
  psql -U crypto_user -d crypto_db -c "SELECT COUNT(*) FROM users;"
```

### Redis Persistence

```bash
# Check Redis persistence status
kubectl exec redis-0 -n crypto -- redis-cli BGSAVE

# Backup Redis dump
kubectl cp crypto/redis-0:/data/dump.rdb ./redis-dump-backup.rdb

# Restore Redis from dump
kubectl cp ./redis-dump-backup.rdb crypto/redis-0:/data/dump.rdb
kubectl delete pod redis-0 -n crypto  # Trigger restart
```

### Kubernetes Resource Backup

```bash
#!/bin/bash
# Backup all Kubernetes resources

BACKUP_DIR=/backups/kubernetes

# Export all resources
kubectl get all --all-namespaces -o yaml > \
  $BACKUP_DIR/all-resources-$(date +%Y%m%d).yaml

# Export specific resources
kubectl get configmaps -n crypto -o yaml > \
  $BACKUP_DIR/configmaps-$(date +%Y%m%d).yaml

kubectl get secrets -n crypto -o yaml > \
  $BACKUP_DIR/secrets-$(date +%Y%m%d).yaml

# Store in version control (encrypted)
git add $BACKUP_DIR
git commit -m "Backup: Kubernetes resources $(date +%Y%m%d)"
```

---

## Performance Tuning

### Database Query Optimization

```bash
# Enable query logging
kubectl exec postgres-0 -n crypto -- psql -U crypto_user -d crypto_db <<EOF
ALTER SYSTEM SET log_min_duration_statement = 500;  # Log queries > 500ms
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();
EOF

# Analyze slow queries
kubectl exec postgres-0 -n crypto -- psql -U crypto_user -d crypto_db -c \
  "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Add missing indexes
kubectl exec postgres-0 -n crypto -- psql -U crypto_user -d crypto_db -c \
  "CREATE INDEX idx_prices_coin_timestamp ON prices(coin_id, timestamp DESC);"

# Vacuum and analyze
kubectl exec postgres-0 -n crypto -- psql -U crypto_user -d crypto_db -c \
  "VACUUM ANALYZE;"
```

### Application Performance Optimization

```bash
# Monitor pod resource usage
kubectl top pods -n crypto --containers --sort-by=memory

# Profile slow endpoints
# Add to Flask/FastAPI:
# @app.middleware("http")
# async def timing_middleware(request, call_next):
#     start = time.time()
#     response = await call_next(request)
#     process_time = time.time() - start
#     response.headers["X-Process-Time"] = str(process_time)
#     return response

# Check response times
kubectl logs deployment/api-gateway -n crypto | grep "X-Process-Time"
```

---

## Security Operations

### Access Control

```bash
# Review RBAC policies
kubectl get rolebindings -n crypto
kubectl get clusterrolebindings

# Create limited service account for monitoring
kubectl create serviceaccount monitoring -n crypto
kubectl create clusterrolebinding monitoring --clusterrole=view --serviceaccount=crypto:monitoring

# Get token for monitoring
kubectl describe secret monitoring-token -n crypto
```

### Secret Rotation

```bash
#!/bin/bash
# Rotate JWT secret

OLD_SECRET=$(kubectl get secret jwt-secret -o jsonpath='{.data.secret}' -n crypto | base64 -d)
NEW_SECRET=$(openssl rand -base64 32)

# Update secret
kubectl patch secret jwt-secret -p "{\"data\":{\"secret\":\"$(echo -n $NEW_SECRET | base64 -w 0)\"}}" -n crypto

# Restart services to apply new secret
kubectl rollout restart deployment/api-gateway -n crypto
kubectl rollout restart deployment/user-service -n crypto

echo "JWT secret rotated"
```

### SSL/TLS Certificate Renewal

```bash
# Check certificate expiry
kubectl get certificate -n crypto

# Renew certificate (let's encrypt)
certbot renew --quiet

# Update secret
kubectl create secret tls tls-secret \
  --cert=/etc/letsencrypt/live/cryptoanalytics.com/fullchain.pem \
  --key=/etc/letsencrypt/live/cryptoanalytics.com/privkey.pem \
  -n crypto --dry-run=client -o yaml | kubectl apply -f -

# Restart Ingress
kubectl rollout restart ingress -n crypto
```

---

## Maintenance Windows

### Planned Maintenance Schedule

- **Weekly (Tuesday 2 AM UTC)**: Database maintenance, index optimization
- **Monthly (First Sunday 3 AM UTC)**: System updates, dependency updates
- **Quarterly**: Full system backup test, disaster recovery drill

### Maintenance Mode

```bash
#!/bin/bash
# Enable maintenance mode

# Create maintenance page
kubectl create configmap maintenance-page --from-file=maintenance.html -n crypto

# Update Ingress to serve maintenance page
kubectl patch ingress api-gateway -p \
  '{"spec":{"rules":[{"http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"maintenance","port":{"number":80}}}}]}}]}}' \
  -n crypto

# Perform maintenance
# ... run your maintenance tasks ...

# Disable maintenance mode
kubectl patch ingress api-gateway -p \
  '{"spec":{"rules":[{"http":{"paths":[{"path":"/","pathType":"Prefix","backend":{"service":{"name":"api-gateway","port":{"number":8000}}}}]}}]}}' \
  -n crypto

echo "Maintenance completed"
```

### Upgrade Procedure

```bash
# Test upgrade in staging first
# Update image versions in k8s manifests
kubectl set image deployment/api-gateway \
  api-gateway=myregistry/api-gateway:v1.1.0 \
  -n crypto

# Monitor rollout
kubectl rollout status deployment/api-gateway -n crypto

# If issues occur, rollback
kubectl rollout undo deployment/api-gateway -n crypto

# Verify health
curl http://api-gateway.crypto.svc:8000/api/health
```

---

## On-Call Escalation

**Primary on-call**: Check PagerDuty schedule
**Escalation**: Engineering Manager -> Engineering Lead -> CTO
**Emergency contact**: ops@example.com, +(1)555-0123

**Incident Review**: Every Monday 10 AM (post-incident RCA)

