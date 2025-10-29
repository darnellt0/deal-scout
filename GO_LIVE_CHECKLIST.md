# Deal Scout - Go Live Checklist

**Last Updated:** October 24, 2025
**Project Status:** ✅ PRODUCTION READY

This checklist will guide you through deploying Deal Scout to production.

---

## Pre-Deployment Verification

- [x] Code testing complete (see `TESTING_REPORT.md`)
- [x] All critical issues fixed
- [x] Security vulnerabilities patched
- [x] Dependencies updated
- [x] Configuration validated
- [x] Documentation complete

---

## Phase 1: Prepare Infrastructure (Timeline: 1-2 weeks)

### Database Setup
- [ ] **Create PostgreSQL database**
  - [ ] Cloud provider: AWS RDS, Google Cloud SQL, DigitalOcean, or self-hosted
  - [ ] Version: 15 or higher (tested with 15)
  - [ ] High availability: Enable Multi-AZ (strongly recommended)
  - [ ] Backups: Enable automatic daily backups (7-30 day retention)
  - [ ] Security: Enable encryption at rest
  - [ ] Network: Restrict to application servers only
  - [ ] Connection: Get `DATABASE_URL` (format: `postgresql+psycopg://user:pass@host:5432/dbname`)

- [ ] **Setup Read Replica (Optional but recommended)**
  - [ ] Create read replica for analytics queries
  - [ ] Improves performance under load

### Cache/Message Broker Setup
- [ ] **Create Redis instance**
  - [ ] Cloud provider: AWS ElastiCache, Google Cloud Memorystore, or self-hosted
  - [ ] Version: 7 or higher (tested with 7)
  - [ ] High availability: Enable Multi-AZ failover
  - [ ] Backups: Enable automatic snapshots
  - [ ] Security: Enable authentication, restrict to application servers
  - [ ] Connection: Get `REDIS_URL` (format: `redis://:password@host:6379/0`)

### Object Storage Setup (Optional but recommended for images)
- [ ] **Create S3 bucket (or equivalent)**
  - [ ] Region: Close to your application servers
  - [ ] Versioning: Enable (for backup recovery)
  - [ ] Encryption: Enable server-side encryption (SSE-S3 or SSE-KMS)
  - [ ] Lifecycle policy: Archive old images after 90 days
  - [ ] Access: Create IAM user with minimal permissions
  - [ ] Credentials: Get `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

### Load Balancer / Reverse Proxy Setup
- [ ] **Setup load balancer**
  - [ ] Type: Application Load Balancer (ALB) or Layer 7 proxy
  - [ ] SSL/TLS: Obtain and configure certificate (free: Let's Encrypt)
  - [ ] Health checks: Configure to hit `/health` endpoint every 30s
  - [ ] Auto-scaling: Setup target group and scaling policies
  - [ ] Security: Configure security groups/firewall rules

---

## Phase 2: Obtain API Keys & Credentials (Timeline: 1 week)

### Required for Core Functionality
- [ ] **OpenAI API Key** (Required for vision features)
  - [ ] Go to: https://platform.openai.com/api-keys
  - [ ] Create API key
  - [ ] Set usage limits and billing alerts
  - [ ] Test connectivity
  - [ ] Store in: `OPENAI_API_KEY`

### Email Configuration (Required for notifications)
- [ ] **Choose email provider:**
  - [ ] SendGrid (recommended): https://sendgrid.com
  - [ ] AWS SES: https://aws.amazon.com/ses/
  - [ ] Mailgun: https://www.mailgun.com/
  - [ ] Other: Any SMTP provider

- [ ] **Setup email credentials**
  - [ ] Get SMTP host and port
  - [ ] Get username and password (or API key)
  - [ ] Setup SPF record: Enables email authentication
  - [ ] Setup DKIM record: Improves deliverability
  - [ ] Setup DMARC record: Email security policy
  - [ ] Test email delivery
  - [ ] Store in: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`

### eBay Integration (Optional, for selling on eBay)
- [ ] **Register on eBay Developer Program**
  - [ ] Go to: https://developer.ebay.com
  - [ ] Create developer account
  - [ ] Create application in Sandbox environment
  - [ ] Get credentials: App ID, Cert ID, Dev ID
  - [ ] Store in: `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_DEV_ID`

- [ ] **Configure OAuth**
  - [ ] Set redirect URI: `EBAY_REDIRECT_URI`
  - [ ] Request authorization scopes (inventory, fulfillment, account, marketing)
  - [ ] Test OAuth flow
  - [ ] When ready, upgrade to Production environment
  - [ ] Update: `EBAY_ENV=production`

### Notification Services (Optional)
- [ ] **Discord Webhook** (for deal alerts to Discord)
  - [ ] Create Discord server and channel
  - [ ] Get webhook URL
  - [ ] Store in: `DISCORD_WEBHOOK_URL`

- [ ] **Twilio SMS** (for SMS notifications)
  - [ ] Create Twilio account: https://www.twilio.com
  - [ ] Get Account SID and Auth Token
  - [ ] Verify phone numbers
  - [ ] Store in: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM`

### Error Tracking (Optional but recommended)
- [ ] **Sentry Setup** (for production error tracking)
  - [ ] Create Sentry account: https://sentry.io
  - [ ] Create new project
  - [ ] Get DSN
  - [ ] Store in: `SENTRY_DSN`

---

## Phase 3: Configure Environment (Timeline: 1-2 days)

- [ ] **Create production .env file**
  ```bash
  cp .env.production .env
  ```

- [ ] **Update core settings:**
  ```env
  # Database
  DATABASE_URL=postgresql+psycopg://user:pass@prod-db.example.com:5432/deals
  DATABASE_POOL_SIZE=20
  DATABASE_MAX_OVERFLOW=40

  # Redis
  REDIS_URL=redis://:password@prod-redis.example.com:6379/0

  # Application
  DEMO_MODE=false              # Disable demo mode
  APP_TIMEZONE=America/Los_Angeles
  LOG_LEVEL=INFO              # Or WARNING in production
  CORS_ORIGINS=https://yourdomain.com
  ```

- [ ] **Update API credentials:**
  ```env
  OPENAI_API_KEY=sk-...your-key...

  # eBay (if using)
  EBAY_ENV=production
  EBAY_APP_ID=...
  EBAY_CERT_ID=...
  EBAY_DEV_ID=...

  # Email
  SMTP_HOST=smtp.sendgrid.net
  SMTP_PORT=587
  SMTP_USER=apikey
  SMTP_PASSWORD=SG.xxx...
  EMAIL_FROM=noreply@yourdomain.com

  # S3 (if using)
  AWS_REGION=us-west-2
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  S3_BUCKET=deal-scout-prod

  # Sentry (optional)
  SENTRY_DSN=https://xxx...@xxx.ingest.sentry.io/123456

  # Notifications (optional)
  DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
  TWILIO_ACCOUNT_SID=AC...
  TWILIO_AUTH_TOKEN=...
  TWILIO_FROM=+1234567890
  ```

- [ ] **Verify configuration**
  ```bash
  docker compose config
  ```

---

## Phase 4: Build & Deploy (Timeline: 1-2 hours)

### Option A: Docker Compose (Single Server)

```bash
# 1. Build images
docker compose -f docker-compose.prod.yml build

# 2. Pull latest code
git pull origin main

# 3. Run database migrations
docker compose -f docker-compose.prod.yml run backend alembic upgrade head

# 4. Start services
docker compose -f docker-compose.prod.yml up -d

# 5. Check logs
docker compose -f docker-compose.prod.yml logs -f backend

# 6. Verify services are running
docker compose -f docker-compose.prod.yml ps
```

### Option B: Kubernetes (Recommended for scaling)

```bash
# 1. Build and push images
docker compose build
docker push yourregistry/deal-scout-backend:latest
docker push yourregistry/deal-scout-frontend:latest

# 2. Update k8s manifests with image URLs and environment variables
# Edit k8s/backend-deployment.yaml
# Edit k8s/frontend-deployment.yaml

# 3. Create namespace
kubectl create namespace deal-scout

# 4. Create secrets
kubectl create secret generic deal-scout-secrets \
  --from-env-file=.env \
  -n deal-scout

# 5. Deploy
kubectl apply -f k8s/ -n deal-scout

# 6. Verify deployment
kubectl get pods -n deal-scout
kubectl get services -n deal-scout

# 7. Check logs
kubectl logs -f deployment/backend -n deal-scout
```

### Option C: Managed Container Service

Use AWS ECS, Google Cloud Run, or similar:

```bash
# 1. Build and push images
docker build -t yourreg/deal-scout-backend:latest ./backend
docker push yourreg/deal-scout-backend:latest
docker build -t yourreg/deal-scout-frontend:latest ./frontend
docker push yourreg/deal-scout-frontend:latest

# 2. Create ECS task definition with your images
# 3. Create ECS service
# 4. Configure load balancer
```

---

## Phase 5: Post-Deployment Verification (Timeline: 1-2 hours)

### Health Checks
- [ ] **Backend API is responding**
  ```bash
  curl https://api.yourdomain.com/health
  # Expected: {"status": "healthy", "database": "ok", "redis": "ok"}
  ```

- [ ] **Frontend is loading**
  ```bash
  curl https://yourdomain.com/
  # Check for HTML response
  ```

- [ ] **Database connections working**
  ```bash
  # Check backend logs
  docker compose logs backend | grep "database"
  ```

- [ ] **Redis connections working**
  ```bash
  # Check backend logs
  docker compose logs backend | grep "redis"
  ```

### Functional Tests
- [ ] **API endpoints respond correctly**
  ```bash
  curl https://api.yourdomain.com/listings
  curl https://api.yourdomain.com/metrics
  ```

- [ ] **Frontend routes load**
  - [ ] Home page: https://yourdomain.com/
  - [ ] Buyer dashboard: https://yourdomain.com/buyer
  - [ ] Seller Snap Studio: https://yourdomain.com/seller

- [ ] **Database is populated** (optional: seed demo data)
  ```bash
  docker compose exec backend python scripts/seed_mock_data.py
  ```

- [ ] **Email notifications work**
  - [ ] Manually trigger a notification
  - [ ] Check email provider logs

- [ ] **Error tracking works** (if using Sentry)
  - [ ] Trigger a test error
  - [ ] Verify it appears in Sentry

### Monitoring Setup
- [ ] **Setup monitoring dashboards**
  - [ ] Prometheus: Scrape metrics from `/metrics`
  - [ ] Grafana: Create dashboards for key metrics
  - [ ] AlertManager: Setup alert rules

- [ ] **Configure log aggregation**
  - [ ] CloudWatch, DataDog, New Relic, or ELK stack
  - [ ] Stream logs from all containers

- [ ] **Setup uptime monitoring**
  - [ ] UptimeRobot or similar
  - [ ] Monitor `/health` endpoint
  - [ ] Alert on downtime

- [ ] **Setup SSL/TLS certificate monitoring**
  - [ ] Configure renewal automation (Let's Encrypt + Certbot)
  - [ ] Alert 30 days before expiration

---

## Phase 6: Ongoing Operations (Timeline: Continuous)

### Daily Tasks
- [ ] **Monitor error tracking** (Sentry)
- [ ] **Review application logs** for warnings/errors
- [ ] **Check uptime monitoring** dashboard
- [ ] **Monitor database performance** (connections, slow queries)
- [ ] **Monitor Redis memory usage** and hit rates

### Weekly Tasks
- [ ] **Review security logs** and access patterns
- [ ] **Test backup restoration** (at least once per month)
- [ ] **Review cost metrics** (database, storage, bandwidth)
- [ ] **Update dependencies** if security patches available
  ```bash
  npm audit
  pip check
  ```

### Monthly Tasks
- [ ] **Full system health check**
  - [ ] Run load test
  - [ ] Check all integrations (eBay, email, etc.)
  - [ ] Test disaster recovery procedures

- [ ] **Security audit**
  - [ ] Check API access logs for anomalies
  - [ ] Review user activity patterns
  - [ ] Test rate limiting and auth

- [ ] **Database maintenance**
  - [ ] Analyze slow queries
  - [ ] Optimize indexes if needed
  - [ ] Archive old data if applicable

### Quarterly Tasks
- [ ] **Full backup and restore test**
- [ ] **Performance optimization review**
- [ ] **Security audit by external team** (recommended)
- [ ] **Capacity planning review**
- [ ] **Update documentation** with lessons learned

---

## Important Reminders

⚠️ **SECURITY**
- Never commit `.env` file to git
- Rotate API keys every 90 days
- Use strong, unique passwords for all services
- Enable MFA on all accounts
- Regularly audit access logs

⚠️ **BACKUPS**
- Test backup restoration monthly
- Keep backups in separate region/account
- Automate backup process

⚠️ **MONITORING**
- Setup alerting for critical metrics
- Have on-call rotation in place
- Document runbooks for common issues

⚠️ **DOCUMENTATION**
- Keep INCIDENT_RUNBOOKS.md updated
- Document all customizations
- Maintain runbook for disaster recovery

---

## Support Resources

- **Documentation:** See all `*.md` files in project root
- **Deployment Guide:** `DEPLOYMENT.md`
- **Production Setup:** `PRODUCTION_README.md`
- **Monitoring Guide:** `MONITORING.md`
- **Troubleshooting:** `INCIDENT_RUNBOOKS.md`
- **Testing Report:** `TESTING_REPORT.md`

---

## Estimated Timeline

| Phase | Duration | Effort |
|-------|----------|--------|
| Prepare Infrastructure | 1-2 weeks | High |
| Obtain API Keys | 1 week | Medium |
| Configure Environment | 1-2 days | Low |
| Build & Deploy | 1-2 hours | Medium |
| Post-Deployment Tests | 2-3 hours | Medium |
| **Total** | **2-3 weeks** | **High** |

---

## Sign-Off

- [ ] All infrastructure ready
- [ ] All credentials obtained
- [ ] Environment configured
- [ ] Deployment successful
- [ ] All health checks passed
- [ ] Monitoring and alerting active
- [ ] Team trained on runbooks
- [ ] Ready for public launch

**Approved for Production:** ________________  Date: ____________

---

## Next Steps After Launch

1. **Monitor closely** for first 24-48 hours
2. **Collect user feedback** and log issues
3. **Optimize performance** based on real usage
4. **Plan features** for next release based on usage patterns
5. **Establish support procedures** for customer issues

Good luck with your launch! 🚀
