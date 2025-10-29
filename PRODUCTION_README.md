# Deal Scout - Production Ready Guide

## Status

✅ **Production-Ready** - Implement remaining checklist items before go-live

### Pre-Deployment Improvements Completed

- ✅ Removed hardcoded credentials from docker-compose.yml
- ✅ Created production environment template (.env.production)
- ✅ Enhanced configuration with validation and logging
- ✅ Implemented production-ready database connection pooling
- ✅ Added retry logic and error handling to notification channels
- ✅ Created comprehensive input validation module
- ✅ Added security headers middleware
- ✅ Created unit and integration tests for critical paths
- ✅ Implemented structured logging configuration
- ✅ Set up Alembic for database migrations
- ✅ Created production deployment guide
- ✅ Created security guidelines document
- ✅ Created monitoring and logging guide

## Quick Start - Development

```bash
# 1. Setup environment
cp .env.example .env

# 2. Start services
docker-compose up -d

# 3. Run tests
docker-compose exec backend pytest backend/tests/ -v

# 4. Access application
# API: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

## Quick Start - Production

```bash
# 1. Prepare environment
cp .env.production .env
# Edit .env with production values (see DEPLOYMENT.md)

# 2. Setup database
docker-compose exec backend alembic upgrade head

# 3. Start services
docker-compose up -d

# 4. Verify deployment
curl http://localhost:8000/health
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                         │
│                      :3000                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                      Load Balancer                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐    ┌────────▼────────┐  ┌────▼────┐
   │Backend 1 │    │  Backend 2      │  │Backend 3│
   │:8000    │    │   :8000         │  │ :8000   │
   └────┬────┘    └────────┬────────┘  └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐    ┌────────▼────────┐  ┌────▼────┐
   │ Worker 1 │    │   Worker 2      │  │ Worker 3│
   │(Celery) │    │  (Celery)       │  │(Celery) │
   └─────────┘    └─────────────────┘  └────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐    ┌────────▼────────┐       │
   │PostgreSQL│    │   Redis         │       │
   │Database  │    │   Cache/Broker  │       │
   └──────────┘    └─────────────────┘       │
                                              │
                                    ┌─────────▼────┐
                                    │  S3/Storage  │
                                    │  (Images)    │
                                    └──────────────┘

Beat Scheduler (Celery Beat)
  ├─ scan_all - Every 5 minutes
  ├─ refresh_comps - Nightly at 3 AM PT
  ├─ reconcile_sales - Hourly
  └─ send_notifications - Hourly
```

## Key Components

### Backend (FastAPI)
- REST API for buyer and seller features
- Real-time marketplace monitoring
- AI-powered image processing and pricing
- Prometheus metrics exposure

### Frontend (Next.js)
- React 18 with TypeScript
- Buyer dashboard with deal discovery
- Seller Snap Studio for photo uploads and pricing

### Celery Workers
- Background task processing
- Scheduled marketplace scans
- Comparable sales refresh
- Sales reconciliation
- Notification dispatch

### Database (PostgreSQL)
- Listings, scores, comparables
- User preferences and accounts
- Snap Studio jobs and results
- Notification history
- Order tracking

### Cache & Message Broker (Redis)
- Task queue for Celery
- Session cache
- Rate limit tracking
- Real-time data caching

## Configuration

### Environment Variables

See `.env.production` template for all options.

**Critical variables:**
```
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://...
OPENAI_API_KEY=sk-...
EBAY_APP_ID=...
EBAY_ENV=production
DEMO_MODE=false
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## API Endpoints

### Health & Metrics
```
GET  /health           - Service health status
GET  /metrics          - Prometheus metrics
```

### Buyer Features
```
GET  /buyer/deals      - List deals with filtering
GET  /listings         - Public listings (deprecated, use /buyer/deals)
```

### Seller Features
```
POST /seller/snap      - Create Snap job (photo upload)
GET  /seller/snap/{id} - Get Snap job status
POST /seller/pricing/suggest - Suggest price
POST /seller/post      - Create listing
```

### eBay Integration
```
GET  /ebay/authorize   - OAuth authorize URL
POST /ebay/exchange    - Exchange auth code for token
```

### Admin/Tasks
```
POST /tasks/scan       - Queue marketplace scan
POST /scan/run         - Trigger scan immediately
POST /tasks/recompute-comps - Refresh comparables
```

## Monitoring & Alerting

### Key Metrics to Monitor

1. **API Health**
   - Request rate
   - Error rate (target: < 1%)
   - Latency (p95 < 500ms)

2. **Task Processing**
   - Queue depth (target: < 100)
   - Task failure rate (target: < 1%)
   - Task duration

3. **System**
   - CPU usage (target: < 70%)
   - Memory usage (target: < 80%)
   - Disk usage (target: > 20% free)

4. **Database**
   - Active connections
   - Query duration (p95 < 100ms)
   - Slow query count

### Alert Thresholds

```
CRITICAL:
  - Error rate > 5%
  - Database unreachable
  - Queue depth > 5000
  - Disk space < 5%

WARNING:
  - Error rate > 1%
  - Latency p95 > 1 second
  - Queue depth > 1000
  - Memory usage > 85%
  - Disk space < 10%
```

See `MONITORING.md` for detailed setup.

## Security Checklist

- [ ] All secrets in environment variables (not hardcoded)
- [ ] HTTPS/TLS enabled
- [ ] Security headers configured
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured
- [ ] CORS properly restricted
- [ ] Database credentials rotated
- [ ] API keys rotated
- [ ] Backups encrypted
- [ ] Audit logging enabled
- [ ] WAF rules configured (if using CDN)

See `SECURITY.md` for detailed guidelines.

## Troubleshooting

### Service Won't Start

1. Check environment variables
   ```bash
   env | grep -E "DATABASE_URL|REDIS_URL"
   ```

2. Check database connectivity
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```

3. Check Redis connectivity
   ```bash
   redis-cli ping
   ```

4. Review logs
   ```bash
   docker-compose logs backend
   ```

### High Error Rate

1. Check health endpoint
   ```bash
   curl http://localhost:8000/health
   ```

2. Review recent errors in logs
   ```bash
   docker-compose logs backend | grep ERROR
   ```

3. Check external dependencies (eBay, OpenAI, etc.)

4. Review database slow query logs

### Task Queue Stuck

```bash
# Check queue depth
redis-cli LLEN celery

# Check active tasks
celery -A app.worker inspect active

# Restart workers
docker-compose restart worker

# Clear failed tasks (use cautiously)
celery -A app.worker purge
```

## Performance Tuning

### Database
- Add indexes for frequently queried columns
- Set appropriate pool size based on concurrent connections
- Enable query logging to identify slow queries

### Caching
- Cache marketplace results for 5 minutes
- Cache comparable sales for 24 hours
- Use Redis for session state

### Frontend
- Enable Gzip compression
- Minify and bundle assets
- Use CDN for static files

### Workers
- Scale workers based on queue depth
- Monitor task duration and optimize slow tasks
- Use task routing if needed (priority queue)

## Backup & Disaster Recovery

### Database Backups
```bash
# Manual backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql

# Automated backups (configure in RDS/Cloud SQL)
# Retention: 7-30 days
```

### Image Storage
- S3 versioning enabled
- Cross-region replication (optional)
- Lifecycle policies for old images

### Recovery Testing
- Weekly test restore from backup
- Document recovery time objective (RTO)
- Document recovery point objective (RPO)

## Upgrade Procedure

```bash
# 1. Create backup
pg_dump $DATABASE_URL > pre_upgrade_backup.sql

# 2. Test in staging
docker-compose -f docker-compose.staging.yml up -d
# Run smoke tests

# 3. Apply database migrations
docker-compose exec backend alembic upgrade head

# 4. Deploy new code
git pull
docker-compose build --no-cache
docker-compose up -d

# 5. Verify deployment
curl http://localhost:8000/health

# 6. Monitor for issues
docker-compose logs -f backend
```

## Support & Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger)
- **Deployment Guide**: See `DEPLOYMENT.md`
- **Security Guidelines**: See `SECURITY.md`
- **Monitoring Setup**: See `MONITORING.md`

## License

Proprietary - Darren's Deal Scout

## Changelog

### Version 0.1.0 (Current)
- Initial production-ready release
- Secure configuration management
- Comprehensive error handling
- Production monitoring setup
- Database migration support
