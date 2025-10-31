# 🚀 Phase 7 Quick Start Guide

**Purpose:** Get Phase 7 up and running in 5 minutes

**Prerequisites:**
- Docker & Docker Compose installed
- Node.js 18+ installed
- npm installed

---

## ⚡ Quick Start (5 Minutes)

### 1. Start Backend Services

```bash
cd deal-scout
docker compose up -d --build backend
```

Expected output:
```
✓ PostgreSQL running
✓ Redis running
✓ Backend API running on http://localhost:8000
```

Verify:
```bash
curl http://localhost:8000/ping
# Should return: {"pong": true, "time": "..."}
```

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

Expected output:
```
✓ Next.js ready on http://localhost:3002
```

### 3. Access the System

**Frontend:**
- Home: http://localhost:3002
- Buyer Dashboard: http://localhost:3002/buyer
- Deal Alerts: http://localhost:3002/buyer/alerts
- Preferences: http://localhost:3002/buyer/preferences

**Backend API:**
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

---

## 🔑 Quick Test (2 Minutes)

### Create Your First Deal Alert

```bash
# 1. Go to http://localhost:3002/buyer/alerts

# 2. Click "New Alert Rule"

# 3. Fill Form:
   Name: "Test Alert"
   Keywords: gaming, laptop
   Max Price: 1000
   Channels: Email ✓

# 4. Click "Create Alert Rule"

# 5. See rule appear in dashboard
```

### Test the Rule

```bash
# 1. Click "Test Rule" on your rule

# 2. See test results modal
   - Shows matching listings from database
   - Reviews criteria matching
   - Close modal

# 3. Success! ✅
```

### Configure Notifications

```bash
# 1. Go to http://localhost:3002/buyer/preferences

# 2. Check "Discord" checkbox

# 3. Click "Add Discord Webhook"

# 4. Enter your Discord webhook URL
   (Get from Discord Server → Webhooks)

# 5. Click "Add Webhook"

# 6. Click "Test Webhook"
   - Should receive test message in Discord
   - Success! ✅
```

---

## 📚 Documentation Files

After quick start, read these in order:

1. **PHASE_7_COMPLETE_SUMMARY.md** - Overview of what was built
2. **PHASE_7_SELLER_WORKFLOW.md** - How sellers benefit
3. **PHASE_7_TIER_1_IMPLEMENTATION.md** - Backend details
4. **PHASE_7_TIER_2_IMPLEMENTATION.md** - Frontend details
5. **PHASE_7_INTEGRATION_TESTING_GUIDE.md** - Comprehensive testing

---

## 🔍 Verify Installation

### Backend Health Check

```bash
curl http://localhost:8000/health | jq .
```

Expected response:
```json
{
  "ok": true,
  "db": true,
  "redis": true,
  "queue_depth": 0,
  "version": "0.1.0"
}
```

### Frontend Running

```bash
curl http://localhost:3002/buyer/alerts 2>&1 | grep -q "html" && echo "✅ Frontend OK"
```

### Database Tables Exist

```bash
docker compose exec backend python -c "
from app.core.models import DealAlertRule, NotificationPreferences, WatchlistItem
print('✅ All tables exist and models loaded')
"
```

### Background Tasks Scheduled

```bash
docker compose exec backend python -c "
from app.worker import celery_app
tasks = list(celery_app.conf.beat_schedule.keys())
for task in tasks:
    if 'deal' in task or 'price' in task:
        print(f'✅ {task} scheduled')
"
```

---

## 🎯 Next Steps After Quick Start

### Immediate (10 min):
1. [ ] Create 2-3 test rules
2. [ ] Test each rule
3. [ ] Configure email notification
4. [ ] Configure Discord webhook
5. [ ] Send test Discord message

### Short Term (30 min):
1. [ ] Read PHASE_7_COMPLETE_SUMMARY.md
2. [ ] Review PHASE_7_TIER_2_IMPLEMENTATION.md
3. [ ] Run PHASE_7_INTEGRATION_TESTING_GUIDE.md scenarios
4. [ ] Test pause/resume/delete operations
5. [ ] Verify quiet hours work

### Medium Term (1-2 hours):
1. [ ] Complete full integration testing
2. [ ] Load test with 10+ rules
3. [ ] Verify background task runs every 30 min
4. [ ] Test all notification channels
5. [ ] Security audit

### Long Term (Production):
1. [ ] Deploy to staging
2. [ ] User acceptance testing
3. [ ] Performance optimization
4. [ ] Deploy to production
5. [ ] Monitor metrics

---

## 🐛 Troubleshooting

### Issue: Backend not responding

```bash
# Check if running
docker compose ps

# Rebuild and restart
docker compose down backend
docker compose up -d --build backend

# Check logs
docker compose logs backend
```

### Issue: Frontend not loading

```bash
# Check if running
ps aux | grep "next dev"

# Kill and restart
pkill -f "next dev"
cd frontend && npm run dev
```

### Issue: Can't create rules (401 error)

```
1. Make sure you're logged in
2. Check browser localStorage has auth_token
3. Try logging out and back in
4. Check token isn't expired
```

### Issue: Rules aren't matching listings

```
1. Verify listings exist in database
2. Check rule criteria are reasonable
3. Try less restrictive keywords
4. Remove exclude keywords temporarily
5. Test with just price filter
```

---

## 📊 Key URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3002 | User interface |
| Buyer Dashboard | http://localhost:3002/buyer | Buyer section |
| Deal Alerts | http://localhost:3002/buyer/alerts | Create/manage rules |
| Preferences | http://localhost:3002/buyer/preferences | Configure notifications |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health Check | http://localhost:8000/health | System status |
| Metrics | http://localhost:8000/metrics | Prometheus metrics |

---

## 🔐 Authentication

### Getting a JWT Token

```bash
# 1. Login via UI at http://localhost:3002
# 2. Token automatically stored in localStorage
# 3. Use in API calls:

curl http://localhost:8000/deal-alert-rules \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Test API Directly

```bash
# Get token (manual - copy from localStorage)
TOKEN="eyJ..."

# List deal alert rules
curl http://localhost:8000/deal-alert-rules \
  -H "Authorization: Bearer $TOKEN"

# Create rule
curl -X POST http://localhost:8000/deal-alert-rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Laptops",
    "keywords": ["gaming", "laptop"],
    "max_price": 800,
    "notification_channels": ["email"]
  }'
```

---

## 📈 Monitoring

### View Backend Logs

```bash
docker compose logs -f backend --tail=50
```

### View Background Task Logs

```bash
docker compose logs -f backend | grep -i "deal_alert\|check_all"
```

### Check Database

```bash
docker compose exec backend python -c "
from app.core.db import get_session
from app.core.models import DealAlertRule
session = get_session()
rules = session.query(DealAlertRule).all()
print(f'Total rules: {len(rules)}')
for rule in rules[:3]:
    print(f'  - {rule.name} ({\"Active\" if rule.enabled else \"Paused\"})')
"
```

---

## 📝 Common Tasks

### Create Rule via API

```bash
TOKEN="your_jwt_token"
curl -X POST http://localhost:8000/deal-alert-rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Budget Gaming Setup",
    "keywords": ["gaming", "pc", "rtx"],
    "exclude_keywords": ["mac", "apple"],
    "min_price": 300,
    "max_price": 1200,
    "categories": ["Electronics"],
    "notification_channels": ["email", "discord"]
  }'
```

### Test Rule via API

```bash
TOKEN="your_jwt_token"
RULE_ID=1
curl -X POST http://localhost:8000/deal-alert-rules/$RULE_ID/test \
  -H "Authorization: Bearer $TOKEN"
```

### Pause Rule via API

```bash
TOKEN="your_jwt_token"
RULE_ID=1
curl -X POST http://localhost:8000/deal-alert-rules/$RULE_ID/pause \
  -H "Authorization: Bearer $TOKEN"
```

### Get Notification Preferences

```bash
TOKEN="your_jwt_token"
curl http://localhost:8000/notification-preferences \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✅ Success Checklist

After completing quick start, you should have:

- [ ] Backend running and responding
- [ ] Frontend running and accessible
- [ ] Created at least 1 deal alert rule
- [ ] Tested the rule (saw matching listings)
- [ ] Configured email notifications
- [ ] Configured Discord notifications
- [ ] Sent test Discord message
- [ ] Reviewed deal alerts dashboard
- [ ] Reviewed notification preferences page
- [ ] Understand the complete flow

---

## 🎓 Learning Resources

After quick start, deepen your knowledge:

1. **Architecture:**
   - Read PHASE_7_COMPLETE_SUMMARY.md for overview
   - Review backend code in backend/app/routes/deal_alerts.py
   - Review frontend code in frontend/app/buyer/alerts/page.tsx

2. **Database:**
   - Check schema in backend/alembic/versions/
   - Review models in backend/app/core/models.py

3. **Background Tasks:**
   - Check scheduling in backend/app/worker.py
   - Review task code in backend/app/tasks/check_deal_alerts.py

4. **API Integration:**
   - Check API client in frontend/lib/api.ts
   - Test endpoints using API docs at http://localhost:8000/docs

---

## 🆘 Need Help?

1. Check PHASE_7_INTEGRATION_TESTING_GUIDE.md for detailed procedures
2. Review backend logs: `docker compose logs -f backend`
3. Check frontend console: Open DevTools (F12) → Console
4. Test API endpoints directly: http://localhost:8000/docs
5. Read relevant documentation files

---

## 📞 Support

For issues:

1. **Backend errors:** Check `docker compose logs backend`
2. **Frontend errors:** Check browser console (F12)
3. **Database issues:** Check PostgreSQL logs
4. **Task issues:** Check Celery logs
5. **API issues:** Check http://localhost:8000/docs

---

**Phase 7 Quick Start - Complete ✅**

You now have a fully functional deal alert system!

Next: Read PHASE_7_COMPLETE_SUMMARY.md for full details.

