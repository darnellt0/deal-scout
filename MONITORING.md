# Monitoring, Logging & Alerting Guide

## Overview

Production-ready monitoring requires observability across metrics, logs, and traces. This guide covers setup and best practices.

## Metrics

### Prometheus Metrics

Deal Scout includes Prometheus-compatible metrics at `/metrics`:

```bash
# View metrics
curl http://localhost:8000/metrics | grep deal_scout
```

Key metrics to track:

- `deal_scout_requests_total` - Total HTTP requests by method, path, status
- `deal_scout_request_duration_seconds` - Request latency (add Prometheus middleware)
- `celery_task_*` - Celery task metrics
- `sqlalchemy_*` - Database query metrics

### Setup Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'deal-scout'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Key Metrics to Monitor

```
# API Performance
request_rate (requests/sec)
error_rate (5xx / total requests)
latency (p50, p95, p99)

# Database
query_duration
active_connections
connection_pool_size
transaction_rollback_rate

# Celery Tasks
task_rate (tasks/sec)
task_duration
task_failure_rate
queue_depth
celery_worker_count

# System
cpu_usage
memory_usage
disk_usage
file_descriptor_usage
```

## Logging

### Application Logging

All logs are structured JSON for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "deal_scout.api",
  "message": "Email sent successfully",
  "request_id": "req_123abc",
  "user_id": "user_456",
  "duration_ms": 245
}
```

### Log Levels

- **DEBUG**: Development only, very verbose
- **INFO**: Normal operation, important events
- **WARNING**: Recoverable issues (retries, degraded service)
- **ERROR**: Errors that need attention (failed requests, exceptions)
- **CRITICAL**: System failures (database down, unable to function)

### Log Configuration

```python
# Configure via environment
LOG_LEVEL=INFO  # Production
LOG_LEVEL=DEBUG # Development

# Log file location
/var/log/deal-scout/app.log
/var/log/deal-scout/celery.log
/var/log/deal-scout/error.log
```

### CloudWatch Logs (AWS)

```python
# Add to application
import watchtower

handler = watchtower.CloudWatchLogHandler(
    log_group='/aws/deal-scout/app',
    stream_name='backend',
)
logging.getLogger().addHandler(handler)
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# filebeat.yml - Ship logs to Elasticsearch
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/deal-scout/*.log
    json.message_key: message
    json.keys_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "deal-scout-%{+yyyy.MM.dd}"
```

## Alerting

### Alert Rules

```yaml
# Alert rules (Prometheus)
groups:
  - name: deal_scout
    rules:
      # API Health
      - alert: HighErrorRate
        expr: rate(deal_scout_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate (> 5%)"
          runbook: "https://wiki/runbooks/high-error-rate"

      # Database
      - alert: DatabaseConnectivityIssue
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection lost"

      # Task Queue
      - alert: HighQueueDepth
        expr: celery_queue_length > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue has {{ $value }} tasks"

      # System Resources
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage > 90%"

      - alert: LowDiskSpace
        expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disk space < 10% free"

      # Application
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(deal_scout_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p95 latency > 500ms"
```

### Notification Channels

```python
# Configure alerting destinations
ALERTMANAGER_SLACK = "https://hooks.slack.com/services/..."
ALERTMANAGER_EMAIL = "alerts@your-domain.com"
ALERTMANAGER_PAGERDUTY = "https://events.pagerduty.com/..."
```

## Distributed Tracing

### OpenTelemetry Setup

```python
# Add to main.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

FastAPIInstrumentor().instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
```

## Dashboard Setup

### Grafana Dashboard Example

```json
{
  "dashboard": {
    "title": "Deal Scout Production",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(deal_scout_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(deal_scout_requests_total{status=~\"5..\"}[5m]) / rate(deal_scout_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(deal_scout_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Queue Depth",
        "targets": [
          {
            "expr": "celery_queue_length"
          }
        ]
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "sqlalchemy_pool_size{job=\"deal-scout\"}"
          }
        ]
      }
    ]
  }
}
```

## Health Checks

### API Health Endpoint

```bash
GET /health

Response:
{
  "ok": true,
  "db": true,
  "redis": true,
  "queue_depth": 42,
  "version": "0.1.0",
  "time": "2024-01-15T10:30:45Z"
}
```

### Liveness Probe (Kubernetes)

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Readiness Probe (Kubernetes)

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Error Tracking

### Sentry Setup

```python
# Add to main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

settings = get_settings()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.05,  # 5% with profiling
        release="deal-scout@0.1.0",
        environment="production",
    )
```

## Performance Profiling

### Temporary Profiling (Development)

```python
from pyinstrument import Profiler

@app.middleware("http")
async def profile_slow_requests(request: Request, call_next):
    if request.url.path.startswith("/slow"):
        profiler = Profiler()
        profiler.start()
        response = await call_next(request)
        profiler.stop()
        print(profiler.output_text(unicode=True, color=True))
        return response
    return await call_next(request)
```

### Production Profiling

Use sampling-based profiling:

```python
# PyFlame
pyflame -o flame.svg -t 60 -s 1 $(pgrep -f "uvicorn")

# py-spy
py-spy record -o profile.svg -- python -m uvicorn app.main:app
```

## Debugging Checklist

When something goes wrong:

1. **Check health endpoint**
   ```bash
   curl -v http://localhost:8000/health
   ```

2. **Review recent logs**
   ```bash
   # Last 100 lines
   docker-compose logs --tail 100 backend

   # Stream logs
   docker-compose logs -f backend
   ```

3. **Check metrics**
   ```bash
   # Request rate
   curl http://localhost:8000/metrics | grep deal_scout_requests

   # Celery queue depth
   redis-cli LLEN celery
   ```

4. **Database connectivity**
   ```bash
   # Test connection
   psql $DATABASE_URL -c "SELECT 1"

   # Check active queries
   psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity"
   ```

5. **Redis connectivity**
   ```bash
   # Test connection
   redis-cli ping

   # Check memory usage
   redis-cli info memory
   ```

6. **Celery worker health**
   ```bash
   # Active tasks
   celery -A app.worker inspect active

   # Worker stats
   celery -A app.worker inspect stats
   ```

## Maintenance

### Daily Tasks
- Review error rate and high latency alerts
- Check queue depth
- Verify backups completed

### Weekly Tasks
- Analyze performance trends
- Review slow query logs
- Update monitoring thresholds if needed

### Monthly Tasks
- Capacity planning (trending up?)
- Security audit logs
- Test disaster recovery

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [ELK Stack](https://www.elastic.co/what-is/elk-stack)
- [Sentry Error Tracking](https://sentry.io/)
- [OpenTelemetry](https://opentelemetry.io/)
