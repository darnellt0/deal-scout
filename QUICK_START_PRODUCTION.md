# Quick Start Guide - Deploy to Production

**Read this first. Takes 5 minutes.**

---

## 🚀 Fast Track to Production (2-4 weeks)

### Week 1: Prepare Infrastructure

```bash
# 1. Provision cloud resources
# - PostgreSQL database (RDS, Cloud SQL, or equivalent)
# - Redis cache (ElastiCache, Cloud Memorystore, or equivalent)
# - S3 bucket or equivalent object storage
# - Load balancer (ALB, NLB, or Ingress)
# - SSL certificates

# 2. Create .env file from template
cp .env.production .env

# 3. Fill in production credentials
# Database connection string
# Redis connection string
# API keys (OpenAI, eBay, SMTP, etc.)
```

### Week 2: Deploy Application

#### Option A: Docker Compose (Single Server)
```bash
# Prepare environment
cp .env.production .env
# Edit .env with actual values

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Apply database migrations
docker-compose exec backend alembic upgrade head

# Verify health
curl http://localhost:8000/health
```

#### Option B: Kubernetes (Recommended)
```bash
# Create namespace
kubectl create namespace deal-scout

# Create secrets
kubectl create secret generic deal-scout-secrets \
  --from-env-file=.env \
  -n deal-scout

# Deploy
kubectl apply -f k8s/

# Wait for rollout
kubectl rollout status deployment/backend -n deal-scout

# Apply database migrations
kubectl exec -it deployment/backend -n deal-scout -- alembic upgrade head

# Verify
kubectl get pods -n deal-scout
curl http://<your-domain>/health
```

### Week 3: Test & Validate

```bash
# Run load tests
pip install locust
locust -f load_test.py --host http://your-domain -u 10 -r 2 -t 5m

# Monitor metrics
# Open Grafana dashboard
# Check Prometheus alerts
# Verify Sentry is capturing errors

# Test incident response
# Follow runbooks in INCIDENT_RUNBOOKS.md
```

### Week 4: Go Live

```bash
# Final checklist
# See PRODUCTION_READINESS_CHECKLIST.md

# Go live
# Monitor closely for first 24 hours
# Team on standby

# Success!
```

---

## 📁 Key Files

### Documentation
- **FINAL_COMPLETION_SUMMARY.md** - What was done (read this first!)
- **DOCUMENTATION_INDEX.md** - Navigation guide
- **DEPLOYMENT.md** - Detailed deployment guide
- **SECURITY.md** - Security checklist
- **INCIDENT_RUNBOOKS.md** - How to handle problems
- **PRODUCTION_READINESS_CHECKLIST.md** - Pre-launch checklist

### Infrastructure
- **docker-compose.prod.yml** - Production Docker setup
- **nginx.conf** - Reverse proxy configuration
- **k8s/** - Kubernetes manifests (namespace, deployments, RBAC, ingress)

### Configuration
- **.env.production** - Template for production secrets
- **alembic/** - Database migrations
- **prometheus-rules.yml** - Monitoring alerts

### Testing
- **load_test.py** - Load testing suite
- **scripts/optimize_database.sql** - Database optimization

---

## 🔑 Production Environment Variables

### Required
```bash
# Database
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/deals

# Redis
REDIS_URL=redis://:password@host:6379/0

# API Keys
OPENAI_API_KEY=sk-...
EBAY_APP_ID=...
EBAY_CERT_ID=...
EBAY_DEV_ID=...

# Email
SMTP_HOST=smtp.provider.com
SMTP_USER=user
SMTP_PASSWORD=password
EMAIL_FROM=noreply@domain.com
```

### Optional
```bash
# Notifications
DISCORD_WEBHOOK_URL=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM=...

# Cloud Storage
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=...

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

---

## 🎯 Deployment Checklist

- [ ] Infrastructure provisioned (RDS, Redis, S3, LB)
- [ ] `.env.production` filled with real credentials
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Monitoring active (Prometheus + Grafana)
- [ ] Alerts configured (30+ rules)
- [ ] Sentry initialized
- [ ] SSL certificates installed
- [ ] DNS configured
- [ ] Load tests passed
- [ ] Team trained on runbooks
- [ ] On-call rotation scheduled
- [ ] Communication channels ready

---

## ⚠️ Critical Configuration

### Database (CRITICAL)
```bash
# Use managed database (RDS, Cloud SQL)
# Enable automated backups (7+ days)
# Enable encryption at rest
# Use Multi-AZ for high availability
```

### Secrets (CRITICAL)
```bash
# NEVER commit .env file
# Use secrets management (AWS Secrets Manager, Vault)
# Rotate API keys monthly
# Secure backups separately
```

### SSL/TLS (CRITICAL)
```bash
# Use HTTPS everywhere
# Use TLS 1.2+
# Keep certificates updated
# Use strong ciphers
```

---

## 🚨 If Something Goes Wrong

### Service Won't Start
```bash
# Check logs
docker-compose logs backend
# or
kubectl logs deployment/backend -n deal-scout

# Check environment variables
env | grep DATABASE_URL

# Check connectivity
psql $DATABASE_URL -c "SELECT 1"
redis-cli ping
```

### High Error Rate
1. Check `/health` endpoint
2. Review logs (grep ERROR)
3. Follow INCIDENT_RUNBOOKS.md
4. Consider rollback procedure

### Database Issues
See: INCIDENT_RUNBOOKS.md → Database Unreachable

### Task Queue Stuck
See: INCIDENT_RUNBOOKS.md → Task Queue Stuck

---

## 📊 Verify Deployment

```bash
# 1. Health check
curl http://localhost:8000/health | jq .

# 2. Metrics available
curl http://localhost:8000/metrics | head -20

# 3. Database connected
docker-compose exec backend python -c "from app.core.db import engine; print('OK')"

# 4. Tests pass
docker-compose exec backend pytest backend/tests/ -q

# 5. No secrets in logs
docker-compose logs | grep -i "password\|secret\|key" | wc -l
# Should be 0
```

---

## 🎓 Learning Resources

### Before Deployment
1. Read: FINAL_COMPLETION_SUMMARY.md (10 min)
2. Read: DEPLOYMENT.md (30 min)
3. Review: Kubernetes manifests (15 min)
4. Review: Prometheus rules (15 min)

### During Deployment
1. Follow: DEPLOYMENT.md step-by-step
2. Check: Health endpoint after each step
3. Monitor: Logs for errors
4. Verify: All services running

### After Deployment
1. Monitor: Dashboard for 24 hours
2. Run: Load tests
3. Review: Alert rules are firing
4. Test: Incident response procedures

---

## 📞 Need Help?

### Documentation
- **General Questions**: DOCUMENTATION_INDEX.md
- **Deployment Issues**: DEPLOYMENT.md
- **Security Questions**: SECURITY.md
- **Running System**: INCIDENT_RUNBOOKS.md
- **Monitoring Setup**: MONITORING.md

### Quick Lookup
- Production environment: `.env.production` template
- Docker setup: `docker-compose.prod.yml`
- Kubernetes setup: `k8s/` directory
- Monitoring: `prometheus-rules.yml`
- Testing: `load_test.py`

---

## ✅ Success Criteria

Your deployment is successful when:

1. ✅ Health check returns 200
2. ✅ No errors in logs
3. ✅ Metrics being collected
4. ✅ Alerts firing correctly
5. ✅ Database migrations applied
6. ✅ API responding < 500ms p95
7. ✅ Error rate < 1%
8. ✅ All services healthy
9. ✅ Load tests passing
10. ✅ Team can access runbooks

---

## 🎯 Next Steps

1. **Now**: Read FINAL_COMPLETION_SUMMARY.md
2. **This Week**: Review all documentation
3. **Next Week**: Provision infrastructure
4. **Week 2**: Deploy to staging
5. **Week 3**: Run tests and validation
6. **Week 4**: Deploy to production

---

**You're all set! Deal Scout is production ready.**

Good luck with your deployment! 🚀

---

For detailed information, see FINAL_COMPLETION_SUMMARY.md or DOCUMENTATION_INDEX.md
