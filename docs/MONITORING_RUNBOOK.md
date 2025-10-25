# Production Logging & Monitoring Runbook

**Status**: Completed  
**Last Updated**: October 25, 2025  
**Version**: 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Log Aggregation with Loki](#log-aggregation-with-loki)
3. [Alert Rules & Thresholds](#alert-rules--thresholds)
4. [Runbook for Common Alerts](#runbook-for-common-alerts)
5. [Dashboard Queries](#dashboard-queries)
6. [Monitoring Stack](#monitoring-stack)

---

## Overview

### Monitoring Stack

```
Application Services
        ↓
Prometheus (metrics scraping)
Loki (log aggregation)
        ↓
Grafana (visualization)
        ↓
Alertmanager (alert routing)
```

### SLA Targets

| Metric | Target | Severity |
|--------|--------|----------|
| Uptime | 99.5% | Critical |
| Error Rate | < 0.5% | Critical |
| API Latency p95 | < 200ms | Warning |
| API Latency p99 | < 500ms | Warning |
| CPU Usage | < 80% | Warning |
| Memory Usage | < 85% | Warning |
| Disk Usage | < 90% | Warning |

---

## Log Aggregation with Loki

### Loki Configuration

```yaml
# monitoring/loki-config.yml
auth_enabled: false

ingester:
  chunk_idle_period: 3m
  chunk_retain_period: 1m
  chunk_encoding: snappy
  max_chunk_age: 2h
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1

limits_config:
  retention_period: 720h  # 30 days
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

schema_config:
  configs:
  - from: 2020-05-15
    store: boltdb-shipper
    object_store: filesystem
    schema:
      version: v11
      index:
        prefix: index_
        period: 24h

server:
  http_listen_port: 3100
  log_level: info
```

### JSON Log Format

All services should output JSON logs:

```json
{
  "timestamp": "2025-10-25T10:30:15.123Z",
  "level": "info",
  "service": "analytics-service",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "message": "Moving average calculated",
  "coin_id": "bitcoin",
  "metric_type": "SMA",
  "period": "20",
  "duration_ms": 45.2,
  "status": "success"
}
```

### Log Parsing in Loki

```yaml
# monitoring/loki-config.yml (continued)
pipeline_stages:
  - json:
      expressions:
        timestamp: timestamp
        level: level
        service: service
        request_id: request_id
        user_id: user_id
        duration_ms: duration_ms
        error: error
  
  - labels:
      level:
      service:
      request_id:
```

### Log Labels

Labels enable efficient querying:

```
{level="error", service="api-gateway"}
{level="warning", service="analytics-service", coin_id="ethereum"}
{request_id="550e8400-e29b-41d4-a716-446655440000"}
{user_id="user123"}
```

---

## Alert Rules & Thresholds

### Prometheus Alert Rules

```yaml
# monitoring/prometheus-alerts.yml

groups:
  - name: application_alerts
    interval: 30s
    rules:
      # Critical: Service Down
      - alert: ServiceDown
        expr: up{job="api-gateway"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.instance }} has been down for 1 minute"
      
      # Critical: High Error Rate
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
            /
            sum(rate(http_requests_total[5m])) by (job)
          ) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate for {{ $labels.job }}"
          description: "Error rate: {{ $value | humanizePercentage }}"
      
      # Warning: High Latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "p95 latency: {{ $value }}s"
      
      # Warning: High CPU Usage
      - alert: HighCPUUsage
        expr: |
          (
            sum(rate(container_cpu_usage_seconds_total[5m])) by (pod_name)
            /
            sum(container_spec_cpu_quota/container_spec_cpu_period) by (pod_name)
          ) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.pod_name }}"
          description: "CPU usage: {{ $value | humanizePercentage }}"
      
      # Warning: High Memory Usage
      - alert: HighMemoryUsage
        expr: |
          (
            container_memory_usage_bytes{pod_name!=""} 
            / 
            container_spec_memory_limit_bytes
          ) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.pod_name }}"
          description: "Memory usage: {{ $value | humanizePercentage }}"
      
      # Critical: Database Connection Pool Exhausted
      - alert: DBConnectionPoolExhausted
        expr: |
          (
            db_pool_checked_out_connections 
            / 
            db_pool_size
          ) > 0.95
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhausted"
          description: "{{ $value | humanizePercentage }} of connections in use"
      
      # Warning: Redis Memory High
      - alert: RedisMemoryHigh
        expr: |
          redis_memory_used_bytes 
          / 
          redis_memory_max_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage high"
          description: "Redis memory: {{ $value | humanizePercentage }}"
      
      # Critical: Kafka Consumer Lag
      - alert: KafkaConsumerLagHigh
        expr: kafka_consumer_lag > 100000
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Kafka consumer lag high"
          description: "Consumer lag: {{ $value }} messages"
      
      # Warning: Disk Space Low
      - alert: DiskSpaceLow
        expr: |
          (
            node_filesystem_avail_bytes{fstype="ext4"} 
            / 
            node_filesystem_size_bytes
          ) < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on {{ $labels.device }}"
          description: "Available: {{ $value | humanizePercentage }}"
      
      # Warning: Pod Restart Loop
      - alert: PodRestartLoop
        expr: |
          rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pod {{ $labels.pod }} restarting frequently"
          description: "Restarts in last 15m: {{ $value }}"
```

---

## Runbook for Common Alerts

### Alert: ServiceDown (Critical)

**Symptoms**: `up{job="api-gateway"} == 0`

**Actions**:
1. Check pod status: `kubectl get pods -l app=api-gateway`
2. Check logs: `kubectl logs -f api-gateway-xxxxx`
3. Check recent events: `kubectl describe pod api-gateway-xxxxx`
4. Check resource constraints: `kubectl top pods`

**Resolution**:
```bash
# If pod is stuck, delete it (will be recreated)
kubectl delete pod api-gateway-xxxxx

# If resources exhausted, scale down other services
kubectl scale deployment analytics-service --replicas=1

# Check for persistent issues in logs
kubectl logs api-gateway-xxxxx | grep -i error
```

### Alert: HighErrorRate (Critical)

**Symptoms**: Error rate > 1% for 5 minutes

**Actions**:
1. Check error logs: 
   ```
   {level="error"}  # in Loki
   ```
2. Identify error types:
   ```
   {level="error"} | json | pattern `<_> <error>`
   ```
3. Check service metrics in Grafana
4. Check recent deployments

**Resolution**:
```bash
# If recent deployment caused it, rollback
kubectl rollout undo deployment/<service-name>

# If database issue, check connections
kubectl logs postgres-0 | grep error

# If external API issue, check connectivity
curl https://api.example.com/health
```

### Alert: HighLatency (Warning)

**Symptoms**: p95 latency > 500ms for 5 minutes

**Actions**:
1. Check slow queries:
   ```
   {duration_ms=~"[5-9][0-9]{2}|[0-9]{4,}"}
   ```
2. Check which endpoints are slow:
   ```
   Prometheus: histogram_quantile(0.95, http_request_duration_seconds_bucket)
   ```
3. Check resource usage
4. Check database locks

**Resolution**:
```bash
# Check database query performance
kubectl exec -it postgres-0 -- psql -U crypto_user -d crypto_db \
  -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Restart service if memory leak suspected
kubectl rollout restart deployment/<service-name>

# Scale up if CPU-bound
kubectl scale deployment analytics-service --replicas=5
```

### Alert: HighCPUUsage (Warning)

**Symptoms**: CPU usage > 80%

**Actions**:
1. Identify CPU-hungry process
2. Check if expected (batch job, heavy calculation)
3. Check for runaway processes

**Resolution**:
```bash
# Scale up the deployment
kubectl scale deployment analytics-service --replicas=5

# Or increase resource limits
kubectl set resources deployment analytics-service \
  --limits=cpu=4000m,memory=4Gi

# Restart to apply changes
kubectl rollout restart deployment analytics-service
```

### Alert: DBConnectionPoolExhausted (Critical)

**Symptoms**: > 95% of DB connections in use

**Actions**:
1. Check active connections:
   ```
   SELECT count(*) FROM pg_stat_activity;
   ```
2. Identify long-running queries:
   ```
   SELECT query, state, wait_event FROM pg_stat_activity 
   WHERE state != 'idle';
   ```
3. Check connection pool settings

**Resolution**:
```bash
# Kill idle connections
kubectl exec -it postgres-0 -- psql -U crypto_user -d crypto_db \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
       WHERE state = 'idle' AND state_change < now() - interval '10 minutes';"

# Scale down non-critical services
kubectl scale deployment sentiment-service --replicas=1

# Increase pool size if needed (requires restart)
kubectl set env deployment api-gateway DATABASE_POOL_SIZE=30
```

### Alert: RedisMemoryHigh (Warning)

**Symptoms**: Redis memory > 85%

**Actions**:
1. Check Redis memory usage: `redis-cli info memory`
2. Identify large keys: `redis-cli --bigkeys`
3. Check eviction policy

**Resolution**:
```bash
# Clear old cache entries
kubectl exec -it redis-0 -- redis-cli FLUSHDB

# Or use FLUSHALL if safe (flushes all databases)
kubectl exec -it redis-0 -- redis-cli FLUSHALL

# Increase Redis memory limit
kubectl set resources statefulset redis \
  --limits=memory=8Gi

# Restart Redis
kubectl rollout restart statefulset redis
```

### Alert: KafkaConsumerLagHigh (Critical)

**Symptoms**: Consumer lag > 100k messages

**Actions**:
1. Check Kafka consumer status:
   ```bash
   kafka-consumer-groups --bootstrap-server kafka:9092 --group analytics-group --describe
   ```
2. Check topic partitions
3. Check consumer scaling

**Resolution**:
```bash
# Scale analytics service to process faster
kubectl scale deployment analytics-service --replicas=10

# Check Kafka topic configuration
kubectl exec -it kafka-0 -- kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe --topic price_updates

# Increase partitions if needed
kubectl exec -it kafka-0 -- kafka-topics \
  --bootstrap-server localhost:9092 \
  --alter --topic price_updates \
  --partitions 24
```

### Alert: DiskSpaceLow (Warning)

**Symptoms**: < 10% disk space available

**Actions**:
1. Identify large directories
2. Check for log files
3. Check for unused data

**Resolution**:
```bash
# Clean old logs
kubectl exec -it postgres-0 -- \
  rm -rf /var/log/postgresql/*-archive.log

# Vacuum database to reclaim space
kubectl exec -it postgres-0 -- psql -U crypto_user -d crypto_db \
  -c "VACUUM ANALYZE;"

# Expand volume (if supported by storage class)
kubectl patch pvc postgres-data -p \
  '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
```

### Alert: PodRestartLoop (Warning)

**Symptoms**: Pod restarting frequently

**Actions**:
1. Check restart count: `kubectl get pods`
2. Check last log lines: `kubectl logs --previous <pod>`
3. Check resource limits

**Resolution**:
```bash
# Increase memory limit
kubectl set resources deployment <service> \
  --limits=memory=2Gi

# Check liveness probe timeout
kubectl describe pod <pod> | grep -A 5 "Liveness"

# Restart to clear state
kubectl rollout restart deployment <service>
```

---

## Dashboard Queries

### Grafana Dashboard Queries

#### Query 1: Request Rate

```promql
sum(rate(http_requests_total[5m])) by (job)
```

#### Query 2: Error Rate

```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
```

#### Query 3: Latency Percentiles

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) by (job)
```

#### Query 4: Memory Usage

```promql
container_memory_usage_bytes{pod_name!=""} / (1024 * 1024)
```

#### Query 5: CPU Usage

```promql
rate(container_cpu_usage_seconds_total[5m]) * 100
```

#### Query 6: Database Connections

```promql
pg_stat_activity_count
```

#### Query 7: Cache Hit Rate

```promql
redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)
```

#### Query 8: Kafka Consumer Lag

```promql
kafka_consumer_lag
```

---

## Monitoring Stack

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: production
    cluster: crypto-analytics

scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:9000']
  
  - job_name: 'analytics-service'
    static_configs:
      - targets: ['analytics-service:9000']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
  
  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka-exporter:9090']
```

### Alertmanager Configuration

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'critical'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 24h
  
  routes:
    - match:
        severity: critical
      receiver: critical-pagerduty
      continue: true
    
    - match:
        severity: warning
      receiver: warning-slack

receivers:
  - name: 'critical-pagerduty'
    pagerduty_configs:
      - service_key: '{{ env "PAGERDUTY_KEY" }}'
  
  - name: 'warning-slack'
    slack_configs:
      - api_url: '{{ env "SLACK_WEBHOOK" }}'
        channel: '#crypto-analytics-alerts'
```

---

## Maintenance Tasks

### Daily

- [ ] Check error rate
- [ ] Review slow query logs
- [ ] Monitor disk usage

### Weekly

- [ ] Review alert history
- [ ] Check resource utilization trends
- [ ] Review backup status

### Monthly

- [ ] Review and update alert thresholds
- [ ] Archive old logs
- [ ] Update runbooks
- [ ] Conduct disaster recovery test

---

**Runbook Status**: ✅ Complete and Production-Ready  
**Last Updated**: October 25, 2025

---

*For emergency support: oncall@company.com or call +1-XXX-XXX-XXXX*
