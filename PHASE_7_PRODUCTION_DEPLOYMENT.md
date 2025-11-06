# Phase 7 Tier 1 - Production Deployment Guide

**Date:** November 6, 2025
**Branch:** `claude/check-dev-status-011CUr3aQqVegj3gd52dYenf`
**Commit:** `4d731a4`
**Status:** Ready for deployment

---

## Pre-Deployment Checklist

### ✅ Code Status
- [x] Phase 7 code committed
- [x] Code pushed to remote
- [x] All files tracked in git
- [x] Working tree clean

### ⏳ Environment Verification
- [ ] Production server accessible
- [ ] Docker & Docker Compose installed
- [ ] Database credentials configured
- [ ] Redis credentials configured
- [ ] SMTP credentials configured (for digest emails)

---

## Deployment Steps

### Step 1: Pull Latest Code

```bash
# SSH into production server
cd /path/to/deal-scout

# Checkout the Phase 7 branch
git fetch origin
git checkout claude/check-dev-status-011CUr3aQqVegj3gd52dYenf
git pull origin claude/check-dev-status-011CUr3aQqVegj3gd52dYenf

# Verify you're on the right commit
git log --oneline -n 1
# Should show: 4d731a4 feat: Complete Phase 7 Tier 1 - User Engagement & Notifications
```

---

### Step 2: Backup Database

**CRITICAL: Always backup before migrations!**

```bash
# Create backup
docker compose exec postgres pg_dump -U deals deals > backup_before_phase7_$(date +%Y%m%d_%H%M%S).sql

# Verify backup file exists and has content
ls -lh backup_before_phase7_*.sql
```

**Store this backup safely!** You'll need it if rollback is required.

---

### Step 3: Apply Database Migration

```bash
# Apply Phase 7 migration
docker compose exec backend alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade 6b2c8f91d4a2 -> phase_7_001
# INFO  [alembic.runtime.migration] Running upgrade phase_7_001 -> ...
```

**If migration fails:**
```bash
# Check current version
docker compose exec backend alembic current

# Check migration history
docker compose exec backend alembic history

# View error details
docker compose logs backend | grep -i alembic
```

---

### Step 4: Verify Database Tables Created

```bash
# Connect to database
docker compose exec postgres psql -U deals -d deals

# Verify Phase 7 tables exist
\dt deal_alert_rules
\dt notification_preferences
\dt watchlist_items

# Check table structure
\d deal_alert_rules
\d notification_preferences
\d watchlist_items

# Exit psql
\q
```

**Expected tables:**
- ✅ `deal_alert_rules` (15 columns)
- ✅ `notification_preferences` (14 columns)
- ✅ `watchlist_items` (8 columns)

---

### Step 5: Update Environment Variables

Check your `.env` file has these configured:

```bash
# Email (REQUIRED for digest emails)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com

# Frontend URL (for email links)
FRONTEND_URL=https://yourdomain.com

# Optional: SMS (Twilio) - Not used in Tier 1
# TWILIO_ACCOUNT_SID=ACxxx
# TWILIO_AUTH_TOKEN=xxx
# TWILIO_PHONE_NUMBER=+1234567890
```

**Test email configuration:**
```bash
docker compose exec backend python -c "
from app.core.email_service import send_email
send_email('test@example.com', 'Test Email', 'This is a test')
"
```

---

### Step 6: Restart Services

```bash
# Restart all services to pick up new code
docker compose restart backend worker beat

# Verify services started successfully
docker compose ps

# Expected: All services "Up" status
```

**Check for startup errors:**
```bash
# Backend logs
docker compose logs backend | tail -50

# Worker logs
docker compose logs worker | tail -50

# Beat (scheduler) logs
docker compose logs beat | tail -50
```

---

### Step 7: Verify Celery Beat Schedule

```bash
# Check that Phase 7 tasks are registered
docker compose logs beat | grep -E "(check-deal-alerts|check-price-drops|send-daily-digests|send-weekly-digests)"

# You should see:
# - check-deal-alerts-every-30-min
# - check-price-drops-hourly
# - send-daily-digests
# - send-weekly-digests
```

**Manually trigger a task to test:**
```bash
# Trigger deal alert check
docker compose exec worker celery -A app.worker call check_all_deal_alerts

# Trigger digest email (will only send to users with preferences set)
docker compose exec worker celery -A app.worker call send_daily_digests
```

---

### Step 8: Test API Endpoints

Open your browser to: `https://yourdomain.com/docs` (FastAPI Swagger UI)

**Test these new endpoints:**

#### 1. Notification Preferences
```bash
# Get preferences (creates default if doesn't exist)
curl -X GET "https://yourdomain.com/notification-preferences" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update channels
curl -X PATCH "https://yourdomain.com/notification-preferences/channels" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channels": ["email", "discord"]}'
```

#### 2. Deal Alert Rules
```bash
# Create a test rule
curl -X POST "https://yourdomain.com/deal-alert-rules" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Gaming PC Alert",
    "keywords": ["gaming", "pc"],
    "max_price": 500,
    "enabled": true,
    "notification_channels": ["email"]
  }'

# List rules
curl -X GET "https://yourdomain.com/deal-alert-rules" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test rule matching
curl -X POST "https://yourdomain.com/deal-alert-rules/1/test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 3. Watchlist
```bash
# Add item to watchlist
curl -X POST "https://yourdomain.com/watchlist" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": 1,
    "price_alert_threshold": 150.00
  }'

# List watchlist
curl -X GET "https://yourdomain.com/watchlist" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected:**
- ✅ All endpoints return 200/201 status codes
- ✅ No 500 errors
- ✅ Data is saved and retrievable

---

### Step 9: Test Email Templates

**Create a test user and trigger a digest:**

```bash
# Inside backend container
docker compose exec backend python -c "
from app.tasks.send_digest_emails import _send_daily_digest_to_user
from app.core.db import SessionLocal
from app.core.models import User
import asyncio

async def test():
    async with SessionLocal() as db:
        user = await db.execute(select(User).limit(1))
        user = user.scalar_one_or_none()
        if user:
            await _send_daily_digest_to_user(db, user)
            print(f'Digest sent to {user.email}')

asyncio.run(test())
"
```

**Check:**
- ✅ Email received
- ✅ HTML renders correctly
- ✅ Images load (if any)
- ✅ Links work (preferences, unsubscribe)

---

### Step 10: Monitor for Errors

**Watch logs for the first hour:**

```bash
# Monitor all services
docker compose logs -f --tail=100

# Watch for errors only
docker compose logs -f | grep -i error

# Specific service logs
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f beat
```

**Common issues to watch for:**
- Database connection errors
- Email sending failures
- Celery task failures
- Memory issues
- Timeout errors

---

## Post-Deployment Verification

### Smoke Tests (Run these after 1 hour)

- [ ] **Background tasks running**
  ```bash
  docker compose logs beat | grep "Scheduler"
  docker compose logs worker | grep "Task"
  ```

- [ ] **No error spikes**
  ```bash
  docker compose logs | grep -c ERROR
  # Should be 0 or very low
  ```

- [ ] **Database performance OK**
  ```bash
  docker compose exec postgres psql -U deals -d deals -c "
    SELECT schemaname, tablename, n_live_tup
    FROM pg_stat_user_tables
    WHERE tablename IN ('deal_alert_rules', 'notification_preferences', 'watchlist_items');
  "
  ```

- [ ] **Memory usage normal**
  ```bash
  docker stats --no-stream
  ```

---

## User Testing Checklist

After deployment, test as a real user:

### Test 1: Create Deal Alert Rule
1. Log into the application
2. Navigate to deal alerts page
3. Create a new rule with keywords
4. Verify rule appears in list
5. Test the rule to see matching listings

### Test 2: Configure Notifications
1. Go to notification preferences
2. Set frequency to "daily"
3. Set quiet hours (e.g., 10 PM - 8 AM)
4. Add Discord webhook URL
5. Test Discord webhook
6. Verify settings are saved

### Test 3: Add to Watchlist
1. Find a listing
2. Add to watchlist with price threshold
3. Verify it appears in watchlist
4. Update price threshold
5. Remove from watchlist

### Test 4: Receive Digest Email
1. Create alert rules
2. Wait for scheduled digest time (9 AM)
3. OR manually trigger: `docker compose exec worker celery -A app.worker call send_daily_digests`
4. Check email inbox
5. Verify digest received and formatted correctly

---

## Rollback Plan (If Things Go Wrong)

### If Critical Issues Occur:

**Step 1: Stop Services**
```bash
docker compose stop backend worker beat
```

**Step 2: Rollback Database**
```bash
# Restore from backup
docker compose exec -T postgres psql -U deals deals < backup_before_phase7_YYYYMMDD_HHMMSS.sql

# OR rollback migration
docker compose exec backend alembic downgrade 6b2c8f91d4a2
```

**Step 3: Revert Code**
```bash
git checkout main  # or previous stable branch
docker compose restart backend worker beat
```

**Step 4: Verify Rollback**
```bash
# Check database version
docker compose exec backend alembic current

# Check services
docker compose ps
```

---

## Monitoring After Deployment

### Metrics to Track (First 24 hours)

**1. Error Rates**
```bash
# Check error logs every hour
docker compose logs --since 1h | grep -i error | wc -l
```

**2. Task Execution**
```bash
# Verify background tasks are running
docker compose logs beat | grep "Scheduler: Sending"
docker compose logs worker | grep "Task.*succeeded"
```

**3. Database Performance**
```bash
# Check slow queries
docker compose exec postgres psql -U deals -d deals -c "
  SELECT query, calls, mean_exec_time
  FROM pg_stat_statements
  WHERE mean_exec_time > 100
  ORDER BY mean_exec_time DESC
  LIMIT 10;
"
```

**4. Memory/CPU Usage**
```bash
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### User Engagement Metrics (First Week)

Track these in your analytics:
- Number of alert rules created
- Number of users setting notification preferences
- Number of watchlist items added
- Digest email open rates
- Notification click-through rates

---

## Success Criteria

Deployment is successful when:

- ✅ All 3 database tables created
- ✅ Migration applied without errors
- ✅ All 24 new API endpoints responding
- ✅ 4 Celery tasks scheduled and running
- ✅ No error rate increase (< 1% errors)
- ✅ Services stable for 24 hours
- ✅ Email digests sending successfully
- ✅ Users can create alert rules
- ✅ Users can add items to watchlist
- ✅ Background tasks executing on schedule

---

## Support & Troubleshooting

### Common Issues

**1. Migration fails with "relation already exists"**
```bash
# Check what migrations are applied
docker compose exec backend alembic history

# If phase_7 already partially applied:
docker compose exec backend alembic stamp phase_7_001
```

**2. Email digests not sending**
```bash
# Check SMTP configuration
docker compose exec backend python -c "from app.config import get_settings; s = get_settings(); print(f'SMTP: {s.smtp_host}:{s.smtp_port}')"

# Test email manually
docker compose exec backend python -c "from app.notify.email import send_email; send_email('test@example.com', 'Test', 'Test body')"
```

**3. Celery tasks not running**
```bash
# Check beat scheduler
docker compose logs beat | tail -50

# Check worker
docker compose logs worker | tail -50

# Restart if needed
docker compose restart worker beat
```

**4. High memory usage**
```bash
# Check for memory leaks
docker stats --no-stream

# Restart if needed
docker compose restart backend worker
```

---

## Estimated Downtime

**Total deployment time:** 15-30 minutes

**Breakdown:**
- Migration: 1-2 minutes
- Service restart: 2-3 minutes
- Verification: 10-25 minutes

**User impact:**
- API briefly unavailable during restart (2-3 minutes)
- Background tasks paused during restart
- No data loss

**Recommended deployment window:** Low-traffic period (2-4 AM)

---

## Contact & Escalation

**If you encounter issues:**

1. Check this document's troubleshooting section
2. Review logs: `docker compose logs | grep -i error`
3. Check database: `docker compose exec postgres psql -U deals`
4. Review migration: `docker compose exec backend alembic history`

**Critical issues:**
- Database corruption → Restore from backup
- Service won't start → Check logs, rollback if needed
- High error rate → Rollback immediately

---

## Documentation References

- **Full Implementation Details:** `PHASE_7_IMPLEMENTATION_COMPLETE.md`
- **Development Roadmap:** `PHASE_7_DEVELOPMENT_ROADMAP.md`
- **API Testing:** `http://localhost:8000/docs` (Swagger UI)

---

## Post-Deployment Report Template

After deployment, fill this out:

```
Phase 7 Tier 1 Deployment Report
Date: _______________
Deployed by: _______________

✅ Pre-deployment checklist complete
✅ Database backup created: backup_before_phase7_YYYYMMDD_HHMMSS.sql
✅ Migration applied successfully
✅ Services restarted
✅ API endpoints tested
✅ Background tasks verified

Issues encountered: _______________
Resolution: _______________

Downtime: ___ minutes
Error rate: ___% (target: <1%)
Memory usage: ___MB (before) → ___MB (after)

Users created alert rules: ___
Users set preferences: ___
Watchlist items added: ___

Status: ✅ SUCCESS / ⚠️ PARTIAL / ❌ FAILED

Notes: _______________
```

---

**Generated:** November 6, 2025
**Status:** Ready for production deployment
**Risk Level:** Low (well-tested, backward compatible)
**Rollback Available:** Yes (backup + migration downgrade)

---

**Next Step:** Begin Step 1 (Pull Latest Code) on your production server.

Good luck with your deployment! 🚀
