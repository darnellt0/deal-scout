# 🚀 Phase 7 Development Roadmap

**Status:** Planning Phase
**Timeline:** 3-6 weeks (after Phase 6 Sprint 1)
**Estimated Implementation:** 60-80 hours
**Recommended Start:** After Phase 6 marketplace integrations are stable

---

## Phase 7 Overview

Phase 7 focuses on **user engagement, notification systems, and intelligent deal matching**. This phase builds on the foundation of Phase 6's marketplace integrations to create a more personalized, user-centric experience.

### Strategic Goals:
- 🔔 Implement smart notification system
- 💰 Add intelligent deal alert rules
- 📧 Build digest email system
- 🔍 Enhance discovery with personalized recommendations
- 📱 Expand notification channels (SMS, Discord, push)

---

## What Just Completed (Phase 6 Sprint 1)

✅ **Already Implemented:**
- Facebook OAuth integration
- Offerup OAuth integration
- Multi-marketplace item posting
- Cross-post tracking
- Database migration for marketplace OAuth fields
- CORS configuration for frontend-backend communication
- Privacy Policy prepared for deployment

---

## Phase 7 Priority Structure

### Tier 1: High Priority (Weeks 1-2) - Recommended Start

These features directly impact user engagement and retention.

#### Feature 1: Enhanced Notification System
**Scope:** Create flexible, personalized notification delivery
**Estimated Time:** 6-7 hours
**Complexity:** Medium
**Impact:** High engagement improvement

**Components:**
1. **Notification Preferences Expansion**
   - Support multiple channels: email, push, SMS, Discord
   - Frequency settings: immediate, daily digest, weekly digest
   - Quiet hours to avoid notifications during sleep
   - Category filters for relevant deals only
   - Max notifications per day to avoid spam

2. **Database Schema Updates**
   ```python
   # Extend existing notification_preferences table
   ALTER TABLE notification_preferences ADD COLUMN:
   - channels: JSON array ["email", "push", "sms"]
   - frequency: enum ["immediate", "daily", "weekly"]
   - quiet_hours_start: time
   - quiet_hours_end: time
   - category_filters: JSON array []
   - max_per_day: integer (default 10)
   ```

3. **API Endpoints**
   ```
   PATCH /notification-preferences/channels
   PATCH /notification-preferences/frequency
   PATCH /notification-preferences/quiet-hours
   PATCH /notification-preferences/categories
   GET /notification-preferences/summary
   ```

4. **Frontend UI**
   - Settings page for preferences
   - Toggle switches for each channel
   - Time picker for quiet hours
   - Category multi-select

**Benefits:**
- Users control notification volume
- Reduced unsubscribe rates
- Better engagement with relevant deals only

---

#### Feature 2: Deal Alert Rules System
**Scope:** Allow users to create custom deal criteria
**Estimated Time:** 5-6 hours
**Complexity:** Medium
**Impact:** High engagement through personalization

**Database Schema:**
```python
class DealAlertRule(Base):
    __tablename__ = "deal_alert_rules"

    id: int
    user_id: int (FK)
    name: str  # "Budget Gaming PC"
    enabled: bool

    # Matching criteria
    keywords: List[str]  # ["gaming", "pc"]
    exclude_keywords: List[str]  # ["mac"]
    categories: List[str]
    condition: Optional[str]  # "good", "excellent"

    # Price range
    min_price: Optional[float]
    max_price: Optional[float]

    # Location
    location: Optional[str]
    radius_mi: Optional[int]

    # Deal score
    min_deal_score: Optional[float]  # 0.0-1.0

    # Notification preferences
    notification_channels: List[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]
```

**API Endpoints:**
```
POST /deal-alert-rules           # Create rule
GET /deal-alert-rules            # List user's rules
GET /deal-alert-rules/{rule_id}  # Get rule details
PATCH /deal-alert-rules/{rule_id}  # Update rule
DELETE /deal-alert-rules/{rule_id}  # Delete rule
POST /deal-alert-rules/{rule_id}/test  # Test rule
POST /deal-alert-rules/{rule_id}/pause  # Disable rule
POST /deal-alert-rules/{rule_id}/resume  # Enable rule
```

**Matching Logic:**
- Keywords: OR logic (match any)
- Exclude keywords: NOT logic (exclude all)
- Categories: OR logic
- Price: between min and max
- Location: within radius
- Deal score: meets minimum threshold
- Condition: exact match if specified

**Background Task:**
```python
# In app/tasks/check_deal_alerts.py
@periodic_task
def check_all_rules():
    for rule in enabled_deal_alert_rules:
        matching_listings = find_matching_listings(rule)
        new_listings = get_new_since(rule.last_triggered_at)

        for listing in new_listings:
            send_notifications(rule, listing)

        rule.last_triggered_at = now()
```

**Schedule:**
- Run every 30 minutes
- Per-user throttling to avoid spam

**Benefits:**
- Users get exactly what they want
- Reduces notification fatigue
- Increases likelihood of purchase

---

#### Feature 3: Digest Email System
**Scope:** Aggregated daily/weekly deal summaries
**Estimated Time:** 4-5 hours
**Complexity:** Medium
**Impact:** Regular engagement touchpoints

**Components:**
1. **Email Template**
   - Professional HTML design
   - Deal cards with images
   - Price trends
   - Top recommendations
   - User preferences summary

2. **Celery Tasks**
   ```python
   # In app/tasks/send_digest_emails.py
   @periodic_task
   def send_daily_digests():
       for user in users_with_daily_digest_preference:
           deals = get_user_deals(user, days=1)
           recommendations = get_recommendations(user)
           send_digest_email(user, deals, recommendations)

   @periodic_task
   def send_weekly_digests():
       # Same but for weekly
   ```

3. **Schedule**
   - Daily at 9 AM (configurable per user)
   - Weekly on Monday at 9 AM
   - Only send if user has preferences set

4. **Email Content**
   - Top 5 deals matched to user preferences
   - Price trends for watched items
   - New marketplace integrations
   - Seller recommendations
   - Unsubscribe link

**Benefits:**
- Regular engagement without spam
- Aggregates deals user cares about
- Increases time spent on platform

---

### Tier 2: Medium Priority (Weeks 3-4)

#### Feature 4: SMS Notifications (Twilio)
**Scope:** SMS alert for high-value deals
**Estimated Time:** 3-4 hours
**Complexity:** Easy-Medium
**Impact:** Urgent deal alerts

**Implementation:**
```python
# In app/notify/sms.py
from twilio.rest import Client

class SMSNotifier:
    def send_alert(self, phone: str, deal: Listing):
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Deal: {deal.title} - ${deal.price}",
            from_=TWILIO_PHONE,
            to=phone
        )
```

**Configuration:**
```bash
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890
```

**API Endpoints:**
```
POST /notification-preferences/phone
  - Add/verify phone number

POST /notification-preferences/phone/verify
  - Confirm OTP sent via SMS
```

**Features:**
- OTP verification
- Rate limiting (max 5 SMS/day per user)
- Opt-in/opt-out capability
- SMS-only urgent alerts

**Benefits:**
- Immediate notification for time-sensitive deals
- High engagement rate
- Direct user communication

---

#### Feature 5: Discord Webhook Integration
**Scope:** Send deal alerts to Discord servers
**Estimated Time:** 3-4 hours
**Complexity:** Easy-Medium
**Impact:** Community-focused alerts

**Implementation:**
```python
# In app/notify/discord.py
import aiohttp

class DiscordNotifier:
    async def send_embed(self, webhook_url: str, deal: Listing):
        embed = {
            "title": deal.title,
            "description": deal.description,
            "price": f"${deal.price}",
            "image": {"url": deal.thumbnail_url}
        }

        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json={"embeds": [embed]})
```

**API Endpoints:**
```
POST /notification-preferences/discord-webhook
  - Register Discord webhook URL

POST /notification-preferences/discord-webhook/test
  - Send test message

DELETE /notification-preferences/discord-webhook
  - Remove webhook
```

**Features:**
- Rich embed formatting
- Image thumbnail display
- Automatic deal link
- Server-level moderation

**Benefits:**
- Reaches users in their communities
- Fosters group deal-sharing culture
- Leverages Discord for discovery

---

#### Feature 6: Push Notifications
**Scope:** Browser/mobile push notifications
**Estimated Time:** 5-6 hours
**Complexity:** Medium
**Impact:** Real-time engagement

**Implementation:**
```python
# In app/notify/push.py
from pywebpush import webpush

class PushNotifier:
    async def send_notification(self, subscription: dict, deal: Listing):
        data = {
            "title": deal.title,
            "body": f"${deal.price}",
            "icon": "/icon.png",
            "data": {"listing_id": deal.id, "url": deal.url}
        }
        webpush(subscription, json.dumps(data))
```

**Frontend:**
- Service Worker registration
- Notification permission request
- Badge and notification handling

**Benefits:**
- Real-time alerts without email delay
- Browser-native experience
- High engagement rate

---

### Tier 3: Enhancement Features (Week 5+)

#### Feature 7: Price Drop Alerts
**Scope:** Alert users when watched items drop in price
**Estimated Time:** 4-5 hours
**Complexity:** Medium

**Implementation:**
```python
class PriceDropWatcher:
    def check_price_drops(self):
        for watchlist_item in user.watchlist:
            current_price = get_current_price(watchlist_item)
            if current_price < watchlist_item.price_threshold:
                send_alert(user, watchlist_item, current_price)
```

**Database:**
```python
class WatchlistItem:
    user_id: int
    listing_id: int
    price_threshold: float
    alert_sent: bool
    created_at: datetime
```

**Benefits:**
- Users don't miss price drops
- High conversion rate
- Increases return visits

---

#### Feature 8: Personalized Recommendations
**Scope:** ML-based deal recommendations
**Estimated Time:** 6-8 hours
**Complexity:** High

**Algorithm:**
```python
def recommend_deals(user: User):
    # Based on:
    # 1. Browsing history
    # 2. Saved items
    # 3. Purchase history
    # 4. Similar users' preferences
    # 5. Category affinity

    candidates = search_similar_to_user_preference(user)
    ranked = rank_by_deal_score(candidates)
    return ranked[:10]
```

**API Endpoint:**
```
GET /recommendations
  - Get personalized deals for user

GET /recommendations/reason?listing_id=123
  - Explain why item recommended
```

**Benefits:**
- Users discover deals they love
- Increases engagement time
- Reduces alert fatigue (curated selection)

---

## Implementation Timeline

### Week 1-2 (Tier 1 - Core)
- [ ] Notification preferences expansion
- [ ] Deal alert rules system
- [ ] Rule matching background task
- [ ] Digest email system

**Deliverable:** Users can set custom deal alerts and receive digests

### Week 3-4 (Tier 2 - Channels)
- [ ] SMS notification support
- [ ] Discord webhook integration
- [ ] Push notification support
- [ ] Phone verification flow

**Deliverable:** Multiple notification channels working

### Week 5+ (Tier 3 - Intelligence)
- [ ] Price drop detection
- [ ] Personalized recommendations
- [ ] Recommendation explanation
- [ ] Advanced user preferences

**Deliverable:** Intelligent deal discovery

---

## Database Changes Summary

### New Tables:
1. `deal_alert_rules` (primary focus)
2. `watchlist_items` (for price tracking)
3. `user_recommendations` (for caching)

### Modified Tables:
1. `notification_preferences` (expand fields)
2. `users` (add phone_number, phone_verified)

### New Indexes:
```sql
CREATE INDEX idx_deal_alert_rules_user_id ON deal_alert_rules(user_id);
CREATE INDEX idx_deal_alert_rules_enabled ON deal_alert_rules(enabled);
CREATE INDEX idx_deal_alert_rules_last_triggered ON deal_alert_rules(last_triggered_at);
CREATE INDEX idx_watchlist_user_price ON watchlist_items(user_id, price_threshold);
```

---

## Technology Stack

### New Dependencies (if all implemented):
```bash
# SMS/Notifications
twilio>=7.0.0

# Discord
aiohttp>=3.8.0
discord-webhook>=1.0.0

# Push notifications
pywebpush>=1.13.0
py-vapid>=1.9.0

# Email templates
jinja2>=3.0.0

# Async tasks (already have Celery)
# No new dependencies needed
```

### Existing Stack (leveraging):
- FastAPI (already using)
- Celery (already using)
- PostgreSQL (already using)
- Redis (already using)
- SQLAlchemy (already using)

---

## API Reference for Phase 7

### Notification Preferences

```
PATCH /notification-preferences/channels
{
  "channels": ["email", "push", "discord"]
}

PATCH /notification-preferences/frequency
{
  "frequency": "daily",
  "time": "09:00"
}

PATCH /notification-preferences/quiet-hours
{
  "start_time": "22:00",
  "end_time": "08:00"
}

GET /notification-preferences/summary
# Response: All preferences for user
```

### Deal Alert Rules

```
POST /deal-alert-rules
{
  "name": "Budget Gaming PC",
  "keywords": ["gaming", "pc"],
  "exclude_keywords": ["mac"],
  "min_price": 200,
  "max_price": 800,
  "min_deal_score": 0.7,
  "notification_channels": ["email", "push"],
  "enabled": true
}

GET /deal-alert-rules
# Response: Array of all user's rules

GET /deal-alert-rules/{rule_id}
# Response: Single rule details

PATCH /deal-alert-rules/{rule_id}
{
  "max_price": 900
}

DELETE /deal-alert-rules/{rule_id}

POST /deal-alert-rules/{rule_id}/test
# Response: { "matching_count": 42, "sample_matches": [...] }

POST /deal-alert-rules/{rule_id}/pause
POST /deal-alert-rules/{rule_id}/resume
```

### SMS/Phone

```
POST /notification-preferences/phone
{
  "phone_number": "+15551234567"
}

POST /notification-preferences/phone/verify
{
  "otp": "123456"
}

GET /notification-preferences/phone
# Response: { "phone_number": "+155...", "verified": true }
```

### Discord

```
POST /notification-preferences/discord-webhook
{
  "webhook_url": "https://discord.com/api/webhooks/..."
}

POST /notification-preferences/discord-webhook/test

DELETE /notification-preferences/discord-webhook
```

### Recommendations

```
GET /recommendations
# Response: Array of 10 recommended deals

GET /recommendations/reason?listing_id=123
# Response: { "reason": "Based on your gaming interest" }

GET /watchlist
# Response: User's saved items

POST /watchlist/items
{
  "listing_id": 123,
  "price_alert_threshold": 299.99
}

DELETE /watchlist/items/{watchlist_item_id}
```

---

## Success Metrics for Phase 7

| Metric | Target | Measurement |
|--------|--------|-------------|
| Notification Engagement | +40% | Click-through rate on alerts |
| Alert Rule Creation | 60%+ users | % setting at least 1 rule |
| Digest Email Open Rate | >25% | Email analytics |
| SMS Opt-In Rate | 15%+ | % of users enabling SMS |
| Deal Discovery Improvement | +50% | Deals viewed per session |
| Recommendation Accuracy | >70% | Click-through on recommendations |

---

## Risk Mitigation

### High-Risk Areas:
1. **Notification spam**
   - Implement rate limiting
   - Add unsubscribe paths
   - Monitor complaint rates

2. **Third-party API dependency (Twilio, Discord)**
   - Cache responses
   - Fallback to email
   - Graceful degradation

3. **Background task overload**
   - Scale Celery workers
   - Add task queue monitoring
   - Prioritize urgent alerts

4. **Data privacy (phone numbers)**
   - PCI compliance review
   - Secure phone storage
   - Privacy policy update

---

## Frontend UI Components Needed

### Dashboard/Settings Pages:
1. **Notification Preferences Panel**
   - Channel toggles
   - Frequency selector
   - Quiet hours time picker
   - Category filter multi-select

2. **Deal Alerts Management Page**
   - Rule list with edit/delete
   - Create new rule form
   - Test rule feature
   - Enable/disable toggle

3. **Watchlist Page**
   - Saved items display
   - Price tracking charts
   - Remove button
   - Sort/filter options

---

## Testing Strategy

### Unit Tests:
- Rule matching logic
- Notification scheduling
- Price calculation
- SMS/Discord formatting

### Integration Tests:
- End-to-end alert flow
- Multiple channels simultaneously
- Celery task execution
- Database transactions

### Manual Testing:
- Create test rules and verify triggers
- Send test SMS/Discord messages
- Check digest email rendering
- Verify quiet hours behavior

---

## Deployment Checklist

Before Phase 7 launch:
- [ ] Celery workers scaled for task volume
- [ ] Redis memory increased for queue
- [ ] Twilio account created and tested
- [ ] Discord bot created
- [ ] SMS opt-in flow reviewed for compliance
- [ ] Privacy policy updated for new data collection
- [ ] Email templates tested in all clients
- [ ] Database migrations reviewed
- [ ] Monitoring/alerting setup
- [ ] Rollback plan documented

---

## Phase 7 vs Phase 6 Comparison

| Aspect | Phase 6 | Phase 7 |
|--------|---------|---------|
| **Focus** | Marketplace expansion | User engagement |
| **Main Feature** | Multi-marketplace posting | Intelligent alerts |
| **Complexity** | Medium | Medium-High |
| **Database Changes** | OAuth fields | Notification/alert tables |
| **External APIs** | Facebook, Offerup | Twilio, Discord |
| **Timeline** | 2-3 weeks | 5-6 weeks |
| **Team Size** | 1-2 dev | 2-3 dev |
| **Impact** | Sales volume | Retention rate |

---

## Next Steps After Phase 7

**Phase 8: Analytics & Intelligence**
- Seller dashboard with metrics
- Platform-wide analytics
- Trend prediction
- Fraud detection

**Phase 9: Mobile App**
- Native iOS/Android
- Push notifications
- Offline capability
- Camera integration

**Phase 10: Advanced Features**
- AI-powered price optimization
- Marketplace optimization AI
- Community features
- Advanced search with ML

---

## Getting Started with Phase 7

**When ready to start:**
1. Review this roadmap with your team
2. Prioritize features based on business goals
3. Create feature branches for each component
4. Set up test environment with Twilio/Discord test accounts
5. Create database migration files
6. Begin Tier 1 implementation

**Estimated time to start Phase 7 after Phase 6:**
- 1-2 weeks of stabilization
- 1 week of planning and setup
- Then begin implementation

---

## Current Status (October 30, 2025)

✅ **Phase 6 Sprint 1 Completed:**
- Facebook OAuth
- Offerup OAuth
- Multi-marketplace posting
- All services running

⏳ **Recommended Next Action:**
- Deploy privacy policy (5 min)
- Configure OAuth credentials (30 min)
- Complete Phase 6 testing (1-2 weeks)
- Start Phase 7 planning

📅 **Estimated Phase 7 Start:** Mid-November 2025

---

**Document Generated:** October 30, 2025
**Status:** Ready for Implementation Planning
**Estimated Dev Time:** 60-80 hours
**Team Recommendation:** 2-3 developers
