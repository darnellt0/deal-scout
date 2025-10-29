# Deal Scout - Production Deployment Guide

## Overview

This guide covers deploying Deal Scout to production with security, reliability, and scalability best practices.

## Pre-Deployment Checklist

### Security
- [ ] All hardcoded credentials removed
- [ ] Production database credentials generated and secured
- [ ] API keys (OpenAI, eBay, Twilio) obtained and verified
- [ ] SMTP credentials configured for production email provider
- [ ] SSL/TLS certificates obtained and configured
- [ ] Database backups configured
- [ ] Secrets stored in secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)

### Infrastructure
- [ ] Managed PostgreSQL database provisioned (AWS RDS, Google Cloud SQL, etc.)
- [ ] Redis cache configured (AWS ElastiCache, Google Cloud Memorystore, etc.)
- [ ] Load balancer configured (optional, for HA)
- [ ] S3 bucket or equivalent object storage created for images
- [ ] CDN configured for static assets (optional)
- [ ] Domain name registered and DNS configured

### Application
- [ ] Environment variables configured from `.env.production` template
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Static files collected
- [ ] Application tested with production credentials
- [ ] Monitoring and logging configured
- [ ] Error tracking (Sentry) configured

### Testing
- [ ] Unit tests pass (`pytest backend/tests`)
- [ ] Integration tests pass with staging database
- [ ] Load testing completed (simulate expected traffic)
- [ ] Backup and recovery tested

## Environment Setup

### 1. Prepare Production Environment Variables

```bash
# Copy the production template
cp .env.production .env

# Edit with production values
vim .env
```

Required variables for production:

```bash
# Database (use managed PostgreSQL)
DATABASE_URL=postgresql+psycopg://user:password@rds-endpoint:5432/deals

# Redis (use managed Redis)
REDIS_URL=redis://:password@elasticache-endpoint:6379/0

# API Keys
OPENAI_API_KEY=sk-xxx...
EBAY_APP_ID=xxx
EBAY_CERT_ID=xxx
EBAY_DEV_ID=xxx
EBAY_ENV=production
EBAY_OAUTH_TOKEN=xxx

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxx...
EMAIL_FROM=noreply@your-domain.com

# Notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/xxx
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_FROM=+1xxx
ALERT_SMS_TO=+1xxx

# Cloud Storage
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAXXX
AWS_SECRET_ACCESS_KEY=xxx
S3_BUCKET=deal-scout-prod
S3_IMAGE_PREFIX=images/

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx

# CORS
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Production Mode
DEMO_MODE=false
```

### 2. Database Setup

```bash
# Install alembic
pip install alembic

# Initialize migrations (one-time)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations to production
alembic upgrade head
```

### 3. Container Deployment

#### Option A: Docker Compose (Single Server)

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f beat
```

#### Option B: Kubernetes (Recommended for HA)

```bash
# Create namespace
kubectl create namespace deal-scout

# Create secrets from .env
kubectl create secret generic deal-scout-secrets \
  --from-env-file=.env \
  -n deal-scout

# Deploy
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check rollout
kubectl rollout status deployment/deal-scout-backend -n deal-scout
```

### 4. Initialize Application

```bash
# Create tables (if not using migrations)
docker-compose exec backend python -c \
  "from app.core.models import Base; from app.core.db import engine; \
   Base.metadata.create_all(bind=engine)"

# Run initial data load (if needed)
docker-compose exec backend python -c \
  "from app.dev_fixtures.loader import load_fixtures; load_fixtures()"

# Verify health check
curl http://localhost:8000/health
```

## Production Deployment Patterns

### High Availability Setup

1. **Load Balancer**: Place behind load balancer (ELB, ALB, nginx)
2. **Multiple Instances**: Run 2+ backend instances
3. **Managed Database**: Use RDS/Cloud SQL for automatic failover
4. **Managed Cache**: Use ElastiCache/Cloud Memorystore
5. **Worker Scaling**: Run multiple Celery workers, 1 beat scheduler

### Monitoring & Alerting

```bash
# Enable Prometheus metrics
curl http://localhost:8000/metrics

# Configure alerts:
# - Health check failures
# - High error rates (> 5% 4xx/5xx)
# - High latency (p95 > 500ms)
# - Queue depth (> 1000 tasks)
# - Low disk space (< 10% free)
# - Database connection pool exhausted
```

### Backup Strategy

```bash
# Automated daily backups (configure in RDS/Cloud SQL)
# Backup retention: minimum 7 days, preferably 30 days

# S3 image storage has versioning enabled
# Database snapshots stored separately from primary instance

# Recovery testing: weekly restore from backup to test environment
```

### Performance Optimization

1. **Database**:
   ```sql
   -- Create indexes for common queries
   CREATE INDEX idx_listings_source_id ON listings(source, source_id);
   CREATE INDEX idx_listing_scores_deal_score ON listing_scores(metric, value DESC);
   CREATE INDEX idx_notifications_status ON notifications(status, created_at);
   ```

2. **Caching**:
   - Cache marketplace results for 5 minutes
   - Cache comparable sales for 24 hours

3. **CDN**: Serve static assets from CDN

## Incident Response

### Common Issues

#### Database Connection Errors
```bash
# Check connection
psql $DATABASE_URL -c "SELECT 1"

# Check pool status
curl http://localhost:8000/health
```

#### Celery Task Failures
```bash
# Check queue depth
redis-cli LLEN celery

# Purge failed tasks (carefully!)
celery -A app.worker purge

# Monitor worker
celery -A app.worker events
```

#### High Memory Usage
```bash
# Check memory by container
docker stats

# Limit memory in docker-compose
# services:
#   backend:
#     memor_limit: 512m
```

### Rollback Procedure

```bash
# Stop current deployment
docker-compose down

# Revert to previous version
git checkout <previous-commit>

# Restart with previous code
docker-compose up -d

# Monitor logs
docker-compose logs -f backend
```

## Monitoring Dashboard

Set up monitoring with Prometheus/Grafana or Datadog:

- Request rate and latency
- Error rate by endpoint
- Database query performance
- Celery task duration and failures
- Redis memory usage
- System CPU and memory
- Disk space usage

## Security Hardening

1. **Network**:
   - Use VPC/security groups to restrict access
   - Only expose API on public internet
   - Keep database in private subnet

2. **Application**:
   - Enable HTTPS only (redirect HTTP → HTTPS)
   - Set secure cookie flags
   - Implement rate limiting

3. **Access Control**:
   - Limit API access to known IPs (if applicable)
   - Enable audit logging
   - Rotate API keys monthly

## Troubleshooting

### View Logs

```bash
# Backend
docker-compose logs backend

# Worker
docker-compose logs worker

# Beat scheduler
docker-compose logs beat

# Follow logs
docker-compose logs -f backend --tail 100
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping

# Celery
celery -A app.worker inspect active
```

### Performance Profiling

```bash
# Add to main.py for production diagnostics
# (Only enable temporarily in production)

from pyinstrument import Profiler

@app.middleware("http")
async def profile_requests(request: Request, call_next):
    profiler = Profiler()
    profiler.start()
    response = await call_next(request)
    profiler.stop()
    print(profiler.output_text(unicode=True, color=True))
    return response
```

## Maintenance

### Regular Tasks

- **Daily**: Monitor health checks, error rates
- **Weekly**: Review logs, test backups
- **Monthly**: Security audit, dependency updates, API key rotation
- **Quarterly**: Performance review, capacity planning

### Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Test in staging first
docker-compose -f docker-compose.staging.yml up -d

# Apply to production after testing
docker-compose build --no-cache
docker-compose up -d
```

## Support

For production issues, escalation path:

1. Check `/health` endpoint for service status
2. Review application logs for errors
3. Check system resources (CPU, memory, disk)
4. Review database performance
5. Contact infrastructure team if needed
