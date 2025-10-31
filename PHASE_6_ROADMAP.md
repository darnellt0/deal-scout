# Deal Scout - Phase 6 Development Roadmap

**Status:** Planning Phase
**Target Timeline:** 4-12 weeks depending on priority selection
**Estimated Implementation Time:** 80-120 hours

---

## Phase 6 Overview

Phase 6 focuses on medium and long-term features that enhance user engagement, marketplace reach, and system intelligence. These features build upon the solid foundation established in Phase 5.

### Strategic Goals:
- 🌐 Expand marketplace reach with additional integrations
- 🔔 Create intelligent, personalized notification system
- 💰 Implement ML-based pricing recommendations
- 📊 Build comprehensive analytics and insights
- 👥 Add social features for community engagement

---

## Priority Tier 1: Short Term (1-2 weeks) - Recommended Start

### Feature 1: Additional Marketplace Integrations

**Scope:** Integrate 2-3 additional marketplaces to expand seller reach

#### 1.1 Facebook Marketplace Integration
**Status:** Adapter exists, ready for integration
**Estimated Time:** 4-5 hours
**Complexity:** Medium

**What's Needed:**
```
Files to Create:
- backend/app/routes/facebook_oauth.py (150 lines)
  - OAuth 2.0 flow for Facebook
  - User authentication

- backend/app/market/facebook_client.py (200 lines)
  - Facebook Graph API client
  - Item posting
  - Image upload
  - Category mapping

Integration Points:
- Extend POST /seller/post to support Facebook
- Update marketplace_accounts routes
- Add Facebook webhook handlers
```

**Key Endpoints:**
- `POST /facebook/authorize` - Start OAuth flow
- `GET /facebook/callback` - Handle OAuth callback
- `POST /facebook/authorize` - Exchange token
- `POST /seller/post?marketplace=facebook` - Post item

**Database:**
- Use existing marketplace_accounts table
- Add facebook_page_id, facebook_access_token fields

**Testing:**
- Test OAuth flow with Facebook sandbox
- Test item posting with images
- Verify category mapping

---

#### 1.2 Offerup Integration
**Status:** Adapter exists, ready for integration
**Estimated Time:** 4-5 hours
**Complexity:** Medium

**What's Needed:**
```
Files to Create:
- backend/app/routes/offerup_oauth.py (120 lines)
- backend/app/market/offerup_client.py (180 lines)
  - Offerup API client
  - Item posting
  - Location-based listing
```

**Key Differences from eBay:**
- Location-based listings
- Mobile-first API
- Simpler authentication
- Different image requirements

---

#### 1.3 Poshmark Integration (New)
**Status:** New integration
**Estimated Time:** 5-6 hours
**Complexity:** Medium-High

**What's Needed:**
```
Files to Create:
- backend/app/routes/poshmark_oauth.py (120 lines)
- backend/app/market/poshmark_client.py (200 lines)
  - Poshmark API client
  - Fashion-specific metadata
  - Bundle support
```

**Special Considerations:**
- Fashion/apparel focused
- Bundle/lot support
- Sharing mechanics
- Social features

---

### Feature 2: Enhanced Notification System

**Scope:** Create intelligent, personalized notification delivery
**Estimated Time:** 6-7 hours
**Complexity:** Medium

**2.1 Notification Preferences Integration**
```
Files to Create/Modify:
- backend/app/routes/notification_preferences.py (ALREADY EXISTS)
  - Add notification channels selection
  - Add frequency settings
  - Add category filters

Database Updates:
- Expand notification_preferences table with:
  - channels: email, push, sms, discord (multi-select)
  - frequency: immediate, daily_digest, weekly_digest
  - quiet_hours: start_time, end_time
  - category_filters: JSON array of categories
  - max_notifications_per_day: integer
```

**API Endpoints to Add:**
```
PATCH /notification-preferences/channels
  - Update which channels to use

PATCH /notification-preferences/frequency
  - Set notification frequency

PATCH /notification-preferences/quiet-hours
  - Set quiet hours (no notifications)

GET /notification-preferences/summary
  - Get current notification settings
```

---

**2.2 Digest Email Rendering**
```
Files to Create:
- backend/app/core/email_templates/digest.html (150 lines)
  - Professional digest email template
  - Deal cards with images
  - Price trends
  - Top recommendations

- backend/app/tasks/send_digest_emails.py (200 lines)
  - Celery task to generate and send digests
  - Aggregates deals from past 24 hours
  - Personalized based on preferences
  - Scheduled execution
```

**Task Schedule:**
```python
# In Celery Beat Config
{
    'send-daily-digest-emails': {
        'task': 'app.tasks.send_digest_emails.send_daily_digests',
        'schedule': crontab(hour=9, minute=0),  # 9 AM
    },
    'send-weekly-digest-emails': {
        'task': 'app.tasks.send_digest_emails.send_weekly_digests',
        'schedule': crontab(day_of_week=0, hour=9, minute=0),  # Monday 9 AM
    },
}
```

---

**2.3 SMS Notifications (Twilio)**
```
Files to Create:
- backend/app/notify/sms.py (150 lines)
  - Twilio integration
  - SMS template service
  - Rate limiting

Dependencies:
- pip install twilio

Configuration:
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890
```

**SMS Templates:**
- Deal alert (short format)
- Order status updates
- Verification codes

---

**2.4 Discord Webhook Integration**
```
Files to Create:
- backend/app/notify/discord.py (120 lines)
  - Discord webhook support
  - Rich message formatting
  - Deal embeds with images

API Endpoint:
POST /notification-preferences/discord-webhook
  - Register Discord webhook URL
  - Test webhook
```

---

### Feature 3: Deal Alert Rules System

**Scope:** Allow users to create custom deal alert criteria
**Estimated Time:** 5-6 hours
**Complexity:** Medium

**3.1 Data Model**
```python
# New Table: deal_alert_rules
class DealAlertRule(Base):
    __tablename__ = "deal_alert_rules"

    id: int (PK)
    user_id: int (FK users)
    name: str  # "Budget Gaming PC Alerts"
    enabled: bool

    # Matching Criteria
    keywords: List[str]  # ["gaming", "pc"] (OR logic)
    exclude_keywords: List[str]  # ["mac"] (NOT logic)
    categories: List[str]
    condition: Optional[str]  # "good", "excellent"

    # Price Criteria
    min_price: Optional[float]
    max_price: Optional[float]

    # Location Criteria
    location: Optional[str]
    radius_mi: Optional[int]

    # Deal Score Criteria
    min_deal_score: Optional[float]  # 0.0-1.0

    # Notification Settings
    notification_channels: List[str]  # ["email", "push"]

    # Metadata
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]
```

**3.2 API Endpoints**
```
POST /deal-alert-rules
  - Create new rule
  - Returns: rule_id, status

GET /deal-alert-rules
  - List all rules for user

GET /deal-alert-rules/{rule_id}
  - Get rule details

PATCH /deal-alert-rules/{rule_id}
  - Update rule criteria

DELETE /deal-alert-rules/{rule_id}
  - Delete rule

POST /deal-alert-rules/{rule_id}/test
  - Test rule with sample listings
  - Returns: matching listings count

POST /deal-alert-rules/{rule_id}/pause
  - Temporarily disable rule

POST /deal-alert-rules/{rule_id}/resume
  - Re-enable rule
```

**3.3 Background Task**
```
Files to Create:
- backend/app/tasks/check_deal_alerts.py (250 lines)
  - Celery task to run periodically (every 30 minutes)
  - For each user's enabled rules:
    - Query listings matching criteria
    - Find new listings since last check
    - Send notifications via preferred channels
    - Update last_triggered_at

Schedule:
{
    'check-deal-alerts': {
        'task': 'app.tasks.check_deal_alerts.check_all_rules',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
```

---

## Priority Tier 2: Medium Term (2-4 weeks)

### Feature 4: ML-Based Pricing Recommendations

**Scope:** Use AI to recommend optimal selling prices
**Estimated Time:** 8-10 hours
**Complexity:** High

**4.1 Price Analysis Engine**
```
Files to Create:
- backend/app/ml/pricing_analyzer.py (300 lines)
  - Analyze similar listings
  - Calculate market avg, median, min, max
  - Identify pricing anomalies
  - Suggest optimal price range

- backend/app/ml/price_predictor.py (250 lines)
  - ML model training (when enough data)
  - Price prediction based on:
    - Item condition
    - Category
    - Market trends
    - Seasonality
```

**4.2 Database Schema**
```python
# New Table: price_analysis
class PriceAnalysis(Base):
    __tablename__ = "price_analysis"

    id: int (PK)
    listing_id: int (FK listings)
    analyzed_at: datetime

    market_avg: float
    market_median: float
    market_min: float
    market_max: float

    comparable_listings: int  # count of similar listings
    recommended_price: float
    price_range_min: float
    price_range_max: float

    # Trend info
    price_trend: str  # "increasing", "stable", "decreasing"
    trend_pct_change: float  # % change in past 30 days
```

**4.3 API Endpoints**
```
POST /listings/{listing_id}/analyze-price
  - Trigger price analysis
  - Returns: market avg, recommendations, comparables

GET /listings/{listing_id}/price-analysis
  - Get cached analysis results

GET /listings/{listing_id}/comparable-listings
  - Get list of similar listings with prices
  - Useful for sellers to see competition

POST /seller/pricing/optimize
  - Batch analyze pricing for seller's items
  - Returns: list with recommendations
```

---

### Feature 5: Advanced Search with Elasticsearch

**Scope:** Replace PostgreSQL search with Elasticsearch for better performance
**Estimated Time:** 10-12 hours
**Complexity:** High

**Why Elasticsearch:**
- ✅ Full-text search with relevance scoring
- ✅ Typo tolerance (fuzzy matching)
- ✅ Synonym support
- ✅ Faceted search
- ✅ Much faster on large datasets (100k+ listings)
- ✅ Phrase queries
- ✅ Aggregations for analytics

**5.1 Implementation**
```
New Dependency:
- pip install elasticsearch

Files to Create:
- backend/app/search/elastic_client.py (250 lines)
  - Elasticsearch connection and operations

- backend/app/search/elastic_indexer.py (200 lines)
  - Celery task to index listings
  - Scheduled sync every hour

- backend/app/tasks/index_listings.py (150 lines)
  - Background task to keep ES in sync

Database Changes:
- Add last_indexed_at to Listing model
- Track indexing status
```

**5.2 API Improvements**
```
Enhancements to existing /listings/search/* endpoints:
- Add fuzzy search parameter (allow typos)
- Add synonym support
- Add faceted results (categories, conditions, etc.)
- Add "did_you_mean" suggestions
- Add search highlighting
- Add relevance scoring
```

**5.3 Docker Compose Update**
```
Add to docker-compose.yml:
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"
```

---

### Feature 6: User Profile Enhancements

**Scope:** Rich user profiles with avatars, ratings, verification
**Estimated Time:** 5-6 hours
**Complexity:** Medium

**6.1 Profile Picture/Avatar Support**
```
Database Changes:
- Add avatar_url: string to User model
- Add avatar_uploaded_at: datetime

Files to Create:
- backend/app/routes/user_profile.py (200 lines)
  - PATCH /users/me/avatar
  - POST /users/me/avatar/upload
  - DELETE /users/me/avatar

- backend/app/core/file_service.py (150 lines)
  - Handle image upload/storage
  - Generate thumbnails
  - Support S3 or local storage
```

**Image Processing:**
```python
from PIL import Image
- Resize to 200x200 (thumbnail)
- Compress quality
- Save as WebP for smaller size
- Store in /static/avatars/ or S3
```

---

**6.2 User Ratings & Reviews**
```
New Tables:
class UserRating(Base):
    __tablename__ = "user_ratings"

    id: int (PK)
    from_user_id: int (FK users)
    to_user_id: int (FK users)

    rating: float (1.0-5.0)
    review_text: Optional[str]

    context: str  # "buyer", "seller", "transaction"
    transaction_id: Optional[int] (FK orders/deals)

    created_at: datetime
    updated_at: datetime

API Endpoints:
POST /users/{user_id}/ratings
  - Leave a rating/review

GET /users/{user_id}/ratings
  - View user's ratings (public)

GET /users/me/ratings/given
  - View ratings I've given (private)

GET /users/{user_id}/rating-summary
  - Get avg rating, count, distribution
```

---

**6.3 User Verification Status**
```
Database Changes:
- Add verification_status to User model
  - "unverified", "email_verified", "phone_verified", "id_verified"

Files to Create:
- backend/app/core/verification_service.py (200 lines)
  - Email verification (already exists via auth)
  - Phone verification (SMS)
  - ID verification (integration with third-party service)

API Endpoints:
POST /users/verify/phone
  - Request phone verification
  - Send OTP via SMS

POST /users/verify/phone/confirm
  - Confirm OTP

GET /users/{user_id}/verification-badge
  - Show verification status publicly
```

---

## Priority Tier 3: Long Term (1-3 months)

### Feature 7: Social Features

**Scope:** Community features to build engagement
**Estimated Time:** 15-20 hours
**Complexity:** High

**7.1 Deal Sharing**
```
New Table: deal_shares
- User can share deals with followers/friends
- Share via link, email, social media

Files:
- backend/app/routes/deal_sharing.py (200 lines)

API:
POST /listings/{listing_id}/share
  - Share via email, link, etc.

GET /shared-deals?token=xyz
  - View shared deal (public, no auth required)
```

**7.2 Community Comments**
```
New Table: listing_comments
- Users comment on deals
- Nested replies support
- Community moderation

Files:
- backend/app/routes/listing_comments.py (250 lines)

API:
POST /listings/{listing_id}/comments
  - Post comment

GET /listings/{listing_id}/comments
  - Get comments with pagination

PATCH /listings/{listing_id}/comments/{comment_id}
  - Edit comment

DELETE /listings/{listing_id}/comments/{comment_id}
  - Delete comment (own only)
```

---

**7.3 Watchlists & Collections**
```
New Tables:
- watchlist_items
- collections

Users can:
- Save deals to watchlist
- Organize deals into collections
- Share collections with others
- Price drop alerts on watchlisted items

API:
POST /watchlist/items
  - Add item to watchlist

GET /watchlist
  - View watchlist

POST /collections
  - Create new collection

PATCH /collections/{id}
  - Update collection

POST /collections/{id}/items
  - Add items to collection
```

---

### Feature 8: Analytics & Reporting Dashboard

**Scope:** Comprehensive insights for sellers and admin
**Estimated Time:** 12-15 hours
**Complexity:** High

**8.1 Seller Dashboard**
```
Metrics:
- Total listings active/sold
- Revenue over time
- Most popular categories
- Price trends
- Seller rating history
- Customer feedback

Files:
- backend/app/routes/seller_analytics.py (300 lines)

API:
GET /seller/analytics/summary
  - Key metrics overview

GET /seller/analytics/listings
  - Listing performance by status

GET /seller/analytics/revenue
  - Revenue analytics by date range

GET /seller/analytics/categories
  - Sales by category

GET /seller/analytics/trends
  - Market trend data for seller's categories
```

**8.2 Admin Dashboard**
```
Metrics:
- Total platform stats
- User growth
- Active listings
- Transaction volume
- Marketplace health
- Top sellers/buyers
- Fraud detection

Files:
- backend/app/routes/admin_analytics.py (250 lines)

API:
GET /admin/analytics/platform
  - Platform-wide metrics

GET /admin/analytics/users
  - User growth, activity

GET /admin/analytics/marketplace
  - Listings, transactions, categories

GET /admin/analytics/health
  - System health metrics
```

**8.3 Reporting & Exports**
```
Features:
- CSV export of analytics
- PDF report generation
- Scheduled report emails
- Custom date ranges

Files:
- backend/app/core/report_generator.py (200 lines)

API:
GET /seller/analytics/export?format=csv
  - Export analytics as CSV

GET /seller/analytics/export?format=pdf
  - Export as PDF report

POST /seller/analytics/schedule-report
  - Schedule periodic reports via email
```

---

## Implementation Priority Recommendation

### Recommended Sequence:

**Phase 6a (Weeks 1-2):**
1. Additional Marketplace Integrations (Facebook + Offerup)
2. Digest Email System
3. Deal Alert Rules

**Phase 6b (Weeks 3-4):**
4. ML-Based Pricing
5. Advanced Search with Elasticsearch
6. User Profile Enhancements

**Phase 6c (Weeks 5+):**
7. Social Features
8. Analytics Dashboard

---

## Development Estimates Summary

| Feature | Effort | Complexity | Estimated Hours | Priority |
|---------|--------|-----------|-----------------|----------|
| Facebook Marketplace | Medium | Medium | 4-5 | Tier 1 |
| Offerup Integration | Medium | Medium | 4-5 | Tier 1 |
| Poshmark Integration | Medium | Medium | 5-6 | Tier 1 |
| Enhanced Notifications | Medium | Medium | 6-7 | Tier 1 |
| Digest Emails | Small | Medium | 3-4 | Tier 1 |
| SMS Notifications | Small | Easy | 2-3 | Tier 1 |
| Discord Webhooks | Small | Easy | 2-3 | Tier 1 |
| Deal Alert Rules | Medium | Medium | 5-6 | Tier 1 |
| ML Pricing | Large | High | 8-10 | Tier 2 |
| Elasticsearch Search | Large | High | 10-12 | Tier 2 |
| User Profiles | Medium | Medium | 5-6 | Tier 2 |
| Social Features | Large | High | 15-20 | Tier 3 |
| Analytics Dashboard | Large | High | 12-15 | Tier 3 |
| **TOTAL** | | | **80-120** | |

---

## Technology Stack Requirements

### New Dependencies (if all implemented):
```
# Phase 6a
# (No new dependencies - uses existing)

# Phase 6b
elasticsearch>=7.0,<8.0
python-jose>=3.3.0
reportlab>=3.6.0  # PDF generation
pandas>=1.3.0  # Data analysis

# Phase 6c
pillow>=8.0.0  # Image processing
twilio>=6.60.0  # SMS
discord-py>=1.7.0  # Discord

pip install -r requirements-phase6.txt
```

---

## Deployment Considerations

### Infrastructure Updates:
- Elasticsearch cluster (for Phase 6b)
- S3 bucket for file storage (for avatars)
- Additional worker nodes for Celery (for scheduled tasks)
- Redis cluster upgrade (for larger task queue)

### External Services:
- Twilio account (for SMS)
- Discord bot token
- Facebook App for OAuth
- Offerup API access
- Poshmark API access

---

## Risk Mitigation

### High-Risk Items:
1. **Elasticsearch migration** - Plan careful rollout
   - Keep PostgreSQL search as fallback
   - Gradual rollout to percentage of users
   - Monitor performance metrics

2. **ML Model accuracy** - Start with simple algorithm
   - Collect pricing data for 2-4 weeks before training
   - Start with heuristic-based recommendations
   - ML models can be added later

3. **Third-party API dependencies** - Add resilience
   - Graceful degradation if API fails
   - Caching of results
   - Fallback options

---

## Success Metrics

### Phase 6 Goals:
- ✅ Increase seller listings by 50% (multi-marketplace)
- ✅ Improve notification engagement by 40% (personalization)
- ✅ Reduce average time-to-sale by 30% (better pricing)
- ✅ Increase user retention by 25% (social features)
- ✅ Platform transaction volume: 10x increase

---

## Next Steps

1. **Review and Select Priority Features**
   - Which Tier 1 features align with business goals?
   - Any urgent marketplace integrations?
   - User feedback on notification preferences?

2. **Allocate Development Resources**
   - Team composition
   - Timeline
   - Budget for external services

3. **Setup Development Environment**
   - Create feature branches
   - Setup testing environments
   - Prepare staging environment

4. **Begin Implementation**
   - Start with Tier 1 features
   - Follow agile sprints (2-week cycles)
   - Regular testing and QA

---

**Document Generated:** October 29, 2025
**Prepared for:** Phase 6 Development Planning
**Status:** Ready for Implementation

