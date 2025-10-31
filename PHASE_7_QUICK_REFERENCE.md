# ⚡ Phase 7 Quick Reference

**Status:** Ready for Planning
**Start Date:** After Phase 6 stabilization (mid-November 2025)
**Duration:** 5-6 weeks
**Team Size:** 2-3 developers

---

## What is Phase 7?

Phase 7 transforms your marketplace into an **intelligent, user-centric notification and deal discovery platform**.

**Main Goal:** Keep users engaged through smart alerts, personalized deals, and multiple notification channels.

---

## The Three Tiers

### 🔴 Tier 1: Core (Weeks 1-2)
**What:** Smart alert system
**Time:** 15-18 hours
**Must-Have:** YES

Features:
- Custom deal alert rules
- Notification preferences (channels, frequency, quiet hours)
- Daily/weekly digest emails
- Background task for rule checking

Result: Users can say "Alert me when gaming PCs drop below $800"

---

### 🟡 Tier 2: Channels (Weeks 3-4)
**What:** More ways to notify
**Time:** 10-12 hours
**Nice-to-Have:** YES

Features:
- SMS notifications (Twilio)
- Discord webhooks
- Push notifications
- Phone verification

Result: Users get alerts via their preferred channel

---

### 🟢 Tier 3: Intelligence (Week 5+)
**What:** Smart recommendations
**Time:** 10-13 hours
**Nice-to-Have:** Later

Features:
- Price drop alerts
- Personalized recommendations
- Advanced user preferences
- Smart filtering

Result: Users discover deals they actually love

---

## Quick Implementation Checklist

### Tier 1: Core Features
```
Deal Alert Rules:
□ Create database table
□ Create CRUD endpoints
□ Implement matching logic
□ Add background task (Celery)
□ Create test script

Notification Preferences:
□ Extend existing table
□ Add preference endpoints
□ Frontend UI
□ Validation

Digest Emails:
□ Create HTML template
□ Create Celery tasks
□ Setup schedule
□ Test rendering
```

### Tier 2: Notification Channels
```
SMS (Twilio):
□ Setup Twilio account
□ Create SMS service
□ Phone verification endpoint
□ Rate limiting

Discord:
□ Create webhook handler
□ Embed formatting
□ Test webhook

Push:
□ Service Worker setup
□ Subscription management
□ Notification display
```

### Tier 3: Intelligence
```
Price Tracking:
□ Watchlist table
□ Price monitoring task
□ Alert trigger

Recommendations:
□ Algorithm design
□ Recommendation endpoint
□ Explanation endpoint
```

---

## Key Numbers

| Item | Count |
|------|-------|
| **New Database Tables** | 2 main (alert_rules, watchlist) |
| **New API Endpoints** | 15-20 |
| **New Background Tasks** | 3-4 |
| **New External Dependencies** | 2-3 (Twilio, Discord) |
| **Frontend Pages/Components** | 3-4 |
| **Estimated Dev Hours** | 60-80 |
| **Estimated Timeline** | 5-6 weeks |

---

## Database at a Glance

### Main Tables to Create/Modify

**1. deal_alert_rules** (NEW)
```
- id (PK)
- user_id (FK)
- name: "Budget Gaming PC"
- keywords: ["gaming", "pc"]
- exclude_keywords: ["mac"]
- min_price: 200
- max_price: 800
- categories: []
- condition: "good"
- location: "San Jose, CA"
- radius_mi: 50
- min_deal_score: 0.7
- notification_channels: ["email", "push"]
- enabled: true
- created_at
- updated_at
- last_triggered_at
```

**2. watchlist_items** (NEW)
```
- id (PK)
- user_id (FK)
- listing_id (FK)
- price_threshold: 299.99
- alert_sent: false
- created_at
```

**3. notification_preferences** (MODIFIED)
```
ADD COLUMNS:
- channels: JSON ["email", "push", "sms"]
- frequency: "daily" | "weekly" | "immediate"
- quiet_hours_start: "22:00"
- quiet_hours_end: "08:00"
- category_filters: JSON []
- max_per_day: 10
```

**4. users** (MODIFIED)
```
ADD COLUMNS:
- phone_number: "+15551234567"
- phone_verified: false
- notification_language: "en"
```

---

## API Endpoints Summary

### Deal Alert Rules
```
POST   /deal-alert-rules           (Create)
GET    /deal-alert-rules           (List)
GET    /deal-alert-rules/{id}      (Get)
PATCH  /deal-alert-rules/{id}      (Update)
DELETE /deal-alert-rules/{id}      (Delete)
POST   /deal-alert-rules/{id}/test (Test)
POST   /deal-alert-rules/{id}/pause
POST   /deal-alert-rules/{id}/resume
```

### Notification Preferences
```
PATCH  /notification-preferences/channels
PATCH  /notification-preferences/frequency
PATCH  /notification-preferences/quiet-hours
GET    /notification-preferences/summary
```

### SMS/Phone
```
POST   /notification-preferences/phone
POST   /notification-preferences/phone/verify
GET    /notification-preferences/phone
```

### Discord
```
POST   /notification-preferences/discord-webhook
POST   /notification-preferences/discord-webhook/test
DELETE /notification-preferences/discord-webhook
```

### Watchlist/Recommendations
```
GET    /watchlist
POST   /watchlist/items
DELETE /watchlist/items/{id}
GET    /recommendations
GET    /recommendations/reason
```

---

## Celery Tasks to Add

```python
# In app/tasks/check_deal_alerts.py
@periodic_task('*/30 * * * *')  # Every 30 minutes
def check_all_rules():
    # Check each enabled rule
    # Match listings
    # Send notifications
    pass

# In app/tasks/send_digest_emails.py
@periodic_task('0 9 * * *')  # Daily at 9 AM
def send_daily_digests():
    # Send email digests
    pass

@periodic_task('0 9 * * 1')  # Weekly Monday 9 AM
def send_weekly_digests():
    # Send weekly digests
    pass

# In app/tasks/check_price_drops.py
@periodic_task('0 * * * *')  # Every hour
def check_price_drops():
    # Check watchlist items
    # Send alerts if price dropped
    pass
```

---

## External Services Needed

### Tier 1
- None (all built-in)

### Tier 2
- **Twilio** (SMS)
  - Account SID
  - Auth Token
  - Phone Number
  - ~$0.01 per SMS

- **Discord** (Webhooks)
  - Already integrated if they use Discord
  - Free

### Tier 3
- None additional

---

## Environment Variables to Add

```bash
# Twilio (for SMS)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# Discord (for webhooks)
# User provides webhook URL directly

# Email (already configured)
# SMTP settings already in place

# Push notifications
VAPID_PUBLIC_KEY=xxx
VAPID_PRIVATE_KEY=xxx
```

---

## Frontend Components Needed

### New Pages
1. **Deal Alerts Management**
   - List all user's rules
   - Create new rule form
   - Edit rule modal
   - Test rule button
   - Enable/disable toggle

2. **Notification Preferences**
   - Channel toggles
   - Frequency selector
   - Quiet hours time pickers
   - Category filters
   - Phone number input
   - Discord webhook input

3. **Watchlist Page** (optional)
   - Saved items list
   - Price tracking chart
   - Remove button
   - Sort options

### Reusable Components
- Rule form (create/edit)
- Channel selector
- Time picker
- Multi-select dropdown
- Price input
- Toggle switches

---

## Testing Strategy

### Unit Tests (per feature)
```
[ ] Rule matching logic
[ ] Notification scheduling
[ ] Preference validation
[ ] Email template rendering
[ ] SMS formatting
[ ] Price calculations
```

### Integration Tests
```
[ ] Alert rule → notification → email
[ ] Alert rule → notification → SMS
[ ] Alert rule → notification → Discord
[ ] Multiple channels simultaneously
[ ] Quiet hours blocking
[ ] Rate limiting
```

### Manual Testing
```
[ ] Create rule and verify trigger
[ ] Receive email notification
[ ] Receive SMS (if configured)
[ ] Receive Discord notification
[ ] Modify preferences and verify
[ ] Pause/resume rule
[ ] Delete rule
```

---

## Common Pitfalls to Avoid

1. **Notification Spam**
   - Always implement rate limiting
   - Respect quiet hours
   - Allow easy unsubscribe
   - Add frequency settings

2. **Background Task Issues**
   - Monitor Celery queue depth
   - Scale workers as needed
   - Implement error handling
   - Log task execution

3. **Third-party API Failures**
   - Have fallback notifications (email)
   - Cache responses
   - Retry logic
   - Circuit breaker pattern

4. **Data Privacy**
   - Phone numbers securely stored
   - Encrypt in transit
   - Follow regional regulations
   - Privacy policy update

---

## Success Criteria

When Phase 7 is complete, you should have:

✅ Users can create custom deal alert rules
✅ Users receive notifications via email
✅ Users receive notifications via SMS (optional)
✅ Users receive notifications via Discord (optional)
✅ Daily/weekly digest emails send automatically
✅ Quiet hours respected globally
✅ Preferences UI fully functional
✅ Alert rules tested and working
✅ No notification spam complaints

---

## Timeline Breakdown

```
Week 1: Database + Core API
  □ Create migrations
  □ Create models
  □ Create CRUD endpoints
  □ Create matching logic

Week 1-2: Background Tasks
  □ Setup Celery task
  □ Implement matching
  □ Test rule triggering

Week 2: Frontend UI
  □ Alert rules page
  □ Preferences page
  □ Create rule form

Week 3: Additional Channels
  □ SMS integration
  □ Discord integration
  □ Push notifications

Week 4: Polish & Testing
  □ Integration testing
  □ Performance tuning
  □ UI improvements

Week 5-6: Intelligence Features
  □ Price tracking
  □ Recommendations
  □ Advanced filtering
```

---

## Dependencies & Cost

### Open-Source (Free)
- FastAPI
- SQLAlchemy
- Celery
- Jinja2
- Aiohttp

### Third-Party Services
| Service | Cost | Required |
|---------|------|----------|
| **Twilio** | $0.01/SMS | Optional |
| **Discord** | Free | Optional |
| **AWS SES** | $0.10 per 1000 emails | For email (optional) |

### Total Monthly Cost
- **Minimum:** $0 (email only)
- **With SMS:** $10-50 (100-5000 SMSs)
- **With all services:** $20-100

---

## Getting Started

### Before You Code:
1. Review this document
2. Read full PHASE_7_DEVELOPMENT_ROADMAP.md
3. Sketch database schema
4. Plan API contracts
5. Design UI mockups

### Day 1:
1. Create feature branch
2. Create database migration
3. Create model classes
4. Write basic tests

### Day 2-3:
1. Implement CRUD endpoints
2. Implement rule matching
3. Create Celery tasks
4. Test basic flow

### Day 4-5:
1. Create frontend UI
2. Wire up frontend to API
3. User testing
4. Bug fixes

---

## Quick Decision Matrix

**Should you do Tier 1?**
- YES - Core feature, high impact

**Should you do Tier 2?**
- YES - If users request SMS/Discord
- NO - If email is sufficient for now

**Should you do Tier 3?**
- YES - If you have ML expertise
- NO - If you want to keep it simple

---

## Resources

### In Your Repo:
- Full Roadmap: `PHASE_7_DEVELOPMENT_ROADMAP.md`
- Database Schemas: In roadmap (copy to migration)
- API Examples: See Tier 1 sections
- Example Celery Task: See deal_alerts task

### External:
- Twilio Docs: https://www.twilio.com/docs
- Discord Webhooks: https://discord.com/developers/docs
- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- Celery: https://docs.celeryproject.io

---

## Questions to Ask Before Starting

1. **User Preferences?**
   - Do users want SMS alerts? (Ask in survey)
   - Do users want Discord? (Check if community uses it)

2. **Budget?**
   - Can we afford Twilio costs?
   - AWS SES vs SendGrid for email?

3. **Timeline?**
   - 5-6 weeks realistic for team?
   - Should we prioritize certain tiers?

4. **Performance?**
   - How many rules per user? (Affects DB query)
   - How often to check rules? (30 min vs 5 min)

---

## Status Summary

| Aspect | Status |
|--------|--------|
| **Phase 6** | ✅ Complete (Sprint 1) |
| **Phase 7** | 📋 Roadmap ready |
| **Phase 7 Start** | ⏳ Mid-November 2025 |
| **Est. Duration** | 5-6 weeks |
| **Team Size** | 2-3 devs |
| **Priority** | High (engagement) |

---

**Document Generated:** October 30, 2025
**Purpose:** Quick reference for Phase 7 planning
**Next Action:** Review with team and prioritize Tier 1 vs 2
