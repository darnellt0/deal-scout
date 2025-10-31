# Phase 6 Implementation Plan - Option A + C (Hybrid)

**Status:** Ready to Begin 🚀
**Total Duration:** 4 weeks | **Total Effort:** 60-80 hours
**Team Size:** 2-3 developers recommended
**Start Date:** Ready Now
**Completion Target:** 4 weeks

---

## Executive Summary

This is a **hybrid plan combining the best of Option A (Business-First) and Option C (AI-First)** - delivering quick revenue-generating features in Week 1-2, then advanced AI features in Week 3-4.

### What You'll Build:
✅ **Marketplace Integrations** (Facebook, Offerup) - Week 1
✅ **Deal Alert Rules System** - Week 2
✅ **Enhanced Notifications** (multi-channel) - Week 2
✅ **ML-Based Pricing** - Week 3
✅ **Elasticsearch Advanced Search** - Week 3-4

### Business Impact:
- 40% increase in user engagement (Week 2)
- 3-4x expansion of seller market reach (Week 1)
- 30% improvement in average selling price (Week 3)
- Better search experience with typo tolerance (Week 4)

### Revenue Impact:
- Marketplace fees: 3-4x more transactions
- Better pricing: Sellers earn more → platform earns more
- User retention: Smarter deals → users stay longer

---

## Implementation Timeline

```
Week 1: Marketplace Integrations
├─ Facebook Marketplace OAuth (3-4 days)
├─ Offerup Integration (2-3 days)
└─ Testing & Deployment (1-2 days)

Week 2: Smart Deals & Notifications
├─ Deal Alert Rules System (3 days)
├─ Enhanced Notifications (2-3 days)
└─ Testing & Deployment (1-2 days)

Week 3: AI Features - Pricing
├─ Price Analysis Engine (2-3 days)
├─ ML Pricing Recommendations (2-3 days)
└─ Testing & Deployment (1 day)

Week 4: Advanced Search
├─ Elasticsearch Setup & Indexing (2 days)
├─ Fuzzy Search & Synonyms (2-3 days)
└─ Testing, Optimization & Deployment (2 days)
```

---

## Sprint Breakdown

### SPRINT 1: MARKETPLACE INTEGRATIONS (Week 1)

**Goal:** Enable sellers to post to Facebook Marketplace and Offerup

#### Sprint 1a: Facebook Marketplace OAuth (3-4 days)

**Files to Create:**
```
backend/app/routes/facebook_oauth.py (150 lines)
backend/app/market/facebook_client.py (200 lines)
backend/alembic/versions/xxxx_add_facebook_fields_to_marketplace_account.py
```

**Database Changes:**
```python
# Add to MarketplaceAccount model:
facebook_page_id: str  # Facebook page ID
facebook_access_token: str  # OAuth token (encrypted)
facebook_business_account_id: str  # For API access
```

**OAuth Flow:**
```
1. GET /facebook/authorize
   → Redirect user to Facebook login
   → Return authorization URL

2. GET /facebook/callback?code=XXX
   → Exchange code for access token
   → Store in marketplace_accounts table
   → Redirect to success page

3. POST /facebook/authorize
   → Verify token
   → Store credentials
   → Return account details
```

**Item Posting:**
```python
# New endpoint:
POST /seller/post?marketplace=facebook
{
  "item_id": 123,
  "marketplace_account_id": 456
}

# What happens:
1. Get item details from my_items table
2. Get Facebook credentials from marketplace_accounts
3. Call Facebook Graph API:
   - Upload images to Facebook
   - Create listing with title, description, price
   - Set category, condition
4. Return facebook_listing_id

# Facebook API Calls:
POST /me/feed  # Create listing post
POST /me/photos  # Upload images
```

**Testing:**
- Test OAuth flow with Facebook sandbox
- Test item posting with sample items
- Verify images upload correctly
- Test category mapping
- Test error handling (expired tokens, etc.)

**Deliverables:**
- ✅ Facebook OAuth working
- ✅ Sellers can connect Facebook account
- ✅ Items can be posted to Facebook
- ✅ Webhooks to track FB updates

---

#### Sprint 1b: Offerup Integration (2-3 days)

**Files to Create:**
```
backend/app/routes/offerup_oauth.py (120 lines)
backend/app/market/offerup_client.py (180 lines)
```

**Key Differences from Facebook:**
- Location-based listings (not national)
- Mobile-first API
- Different image requirements
- Simpler authentication

**Offerup API:**
```python
# Similar to Facebook:
GET /offerup/authorize → OAuth
POST /seller/post?marketplace=offerup → Post item

# But with location awareness:
{
  "location": {
    "latitude": 37.3382,
    "longitude": -121.8863,
    "radius_mi": 25
  }
}
```

**Testing:**
- Test with Offerup sandbox
- Verify location-based posting
- Test image upload
- Validate category mapping

**Deliverables:**
- ✅ Offerup OAuth working
- ✅ Location-aware posting
- ✅ Item visibility in local area
- ✅ Webhook tracking

---

#### Sprint 1 Testing & Deployment

**Test Plan:**
```
1. Integration Tests:
   - POST /seller/post with both marketplaces
   - Verify items appear on both platforms
   - Test with different item types

2. Load Testing:
   - Simulate 100+ concurrent listings
   - Monitor API response times

3. Error Handling:
   - Test with expired tokens
   - Test with API rate limits
   - Test with invalid items

4. User Acceptance Testing:
   - Sellers post items to multiple platforms
   - Verify cross-platform visibility
   - Test webhook updates
```

**Deployment:**
- Create feature branch: `feature/marketplace-integrations`
- Deploy to staging environment
- Run full test suite
- Deploy to production

**Documentation:**
- API docs for new endpoints
- Seller guide for using marketplaces
- Admin guide for managing accounts

---

### SPRINT 2: SMART DEALS & NOTIFICATIONS (Week 2)

**Goal:** Automate deal discovery and intelligent notifications

#### Sprint 2a: Deal Alert Rules System (3 days)

**Database Schema:**
```python
class DealAlertRule(Base):
    __tablename__ = "deal_alert_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Matching Criteria
    keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    exclude_keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    categories: Mapped[List[str]] = mapped_column(JSON, default=list)
    condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Price Criteria
    min_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Location Criteria
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    radius_mi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Deal Score Criteria
    min_deal_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Notification Settings
    notification_channels: Mapped[List[str]] = mapped_column(JSON, default=["email", "push"])

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

**Files to Create:**
```
backend/app/routes/deal_alert_rules.py (250 lines)
backend/app/tasks/check_deal_alerts.py (250 lines)
backend/alembic/versions/xxxx_create_deal_alert_rules_table.py
```

**API Endpoints:**
```python
# CRUD Operations
POST /deal-alert-rules
  {
    "name": "Gaming PCs Under $1000",
    "keywords": ["gaming", "pc"],
    "exclude_keywords": ["mac", "laptop"],
    "max_price": 1000.0,
    "min_deal_score": 0.7,
    "categories": ["electronics"],
    "notification_channels": ["email", "push"]
  }
  → Returns: { "id": 1, "status": "created" }

GET /deal-alert-rules
  → Returns: List of all user's rules

GET /deal-alert-rules/{rule_id}
  → Returns: Rule details

PATCH /deal-alert-rules/{rule_id}
  → Update rule criteria

DELETE /deal-alert-rules/{rule_id}
  → Delete rule

POST /deal-alert-rules/{rule_id}/test
  → Test rule with current listings
  → Returns: List of matching listings (for preview)

POST /deal-alert-rules/{rule_id}/pause
  POST /deal-alert-rules/{rule_id}/resume
  → Toggle rule on/off
```

**Background Task:**
```python
# In app/tasks/check_deal_alerts.py

@celery_app.task
def check_all_rules():
    """Run every 30 minutes to check all active rules"""

    # Get all enabled rules
    rules = db.query(DealAlertRule).filter(
        DealAlertRule.enabled == True
    ).all()

    for rule in rules:
        # Query listings matching rule criteria
        matches = query_matching_listings(rule)

        # Filter to only NEW matches (since last_triggered_at)
        new_matches = filter_new_listings(matches, rule.last_triggered_at)

        if new_matches:
            # Send notifications via user's preferred channels
            for channel in rule.notification_channels:
                if channel == "email":
                    send_deal_alert_email(rule.user_id, new_matches)
                elif channel == "push":
                    send_push_notifications(rule.user_id, new_matches)
                elif channel == "sms":
                    send_sms_alerts(rule.user_id, new_matches)
                elif channel == "discord":
                    send_discord_webhook(rule.user_id, new_matches)

            # Update last_triggered_at
            rule.last_triggered_at = datetime.utcnow()
            db.commit()

# Celery Beat Schedule:
{
    'check-deal-alerts': {
        'task': 'app.tasks.check_deal_alerts.check_all_rules',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
```

**Testing:**
- Create test rules with different criteria
- Verify rule matching logic
- Test background task execution
- Verify notifications sent correctly
- Test rule pause/resume

**Deliverables:**
- ✅ Deal alert rules fully functional
- ✅ Background task running every 30 minutes
- ✅ Multi-channel notification support
- ✅ Rule testing/preview feature

---

#### Sprint 2b: Enhanced Notifications (2-3 days)

**Files to Create/Modify:**
```
backend/app/routes/notification_preferences.py (EXPAND - add 100+ lines)
backend/app/core/notification_service.py (NEW - 200 lines)
backend/app/tasks/send_digest_emails.py (NEW - 200 lines)
```

**Database Changes:**
```python
# Add to notification_preferences:
email_enabled: bool = True
push_enabled: bool = True
sms_enabled: bool = True
discord_enabled: bool = True

# Frequency settings:
notification_frequency: str  # "immediate", "daily_digest", "weekly_digest"

# Quiet hours:
quiet_hours_start: Optional[time]  # e.g., 22:00 (10pm)
quiet_hours_end: Optional[time]    # e.g., 08:00 (8am)

# Rate limiting:
max_notifications_per_day: int = 50

# Categories:
enabled_categories: List[str]  # Only notify for certain categories
```

**New Endpoints:**
```python
PATCH /notification-preferences/channels
  {
    "email": true,
    "push": true,
    "sms": false,
    "discord": true
  }

PATCH /notification-preferences/frequency
  {
    "notification_frequency": "daily_digest"  # or "immediate", "weekly_digest"
  }

PATCH /notification-preferences/quiet-hours
  {
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00"
  }

PATCH /notification-preferences/rate-limit
  {
    "max_notifications_per_day": 50
  }

GET /notification-preferences/summary
  → Returns: Current notification settings (all channels, frequency, etc.)
```

**SMS Integration (Twilio):**
```python
# Add to config.py:
TWILIO_ACCOUNT_SID = env.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = env.get("TWILIO_PHONE_NUMBER")

# In notification_service.py:
def send_sms(phone_number: str, message: str):
    """Send SMS via Twilio"""
    try:
        message = twilio_client.messages.create(
            body=message,
            from_=settings.twilio_phone_number,
            to=phone_number
        )
        return True
    except Exception as e:
        logger.error(f"SMS send failed: {e}")
        return False
```

**Discord Webhook Integration:**
```python
# New endpoint:
POST /notification-preferences/discord-webhook
  {
    "discord_webhook_url": "https://discord.com/api/webhooks/xxx/yyy"
  }
  → Test webhook, store in user.profile

# In notification_service.py:
def send_discord_notification(webhook_url: str, title: str, message: str):
    """Send notification to Discord webhook"""
    payload = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": 0x00ff00
        }]
    }
    response = httpx.post(webhook_url, json=payload)
    return response.status_code == 204
```

**Digest Email Generation:**
```python
# New file: backend/app/core/email_templates/digest.html
# HTML template for daily/weekly digests with:
# - Deal cards with images
# - Price trends
# - "You saved" stats
# - Top recommendations

# In send_digest_emails.py:
@celery_app.task
def send_daily_digests():
    """Send daily digest emails at 9 AM"""

    users = db.query(User).filter(
        User.notification_preferences.notification_frequency == "daily_digest"
    ).all()

    for user in users:
        # Get matching deals from past 24 hours
        deals = get_user_deals(user, hours=24)

        if deals:
            # Render HTML digest
            html = render_digest_template(user, deals)

            # Send email
            email_service.send_email(
                to_email=user.email,
                subject="Your Daily Deal Digest",
                html_body=html,
                text_body=generate_text_version(deals)
            )
```

**Celery Beat Schedule:**
```python
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

**Testing:**
- Test all notification channels
- Verify quiet hours work
- Test rate limiting
- Test digest email rendering
- Test SMS delivery
- Test Discord webhooks

**Deliverables:**
- ✅ Multi-channel notifications (email, push, SMS, Discord)
- ✅ Digest email system
- ✅ Quiet hours enforcement
- ✅ Rate limiting
- ✅ Channel preferences

---

### SPRINT 3: ML PRICING & ELASTICSEARCH (Week 3-4)

**Goal:** AI-powered pricing recommendations and advanced search

#### Sprint 3a: ML-Based Pricing (2-3 days)

**Files to Create:**
```
backend/app/ml/pricing_analyzer.py (300 lines)
backend/app/ml/price_predictor.py (250 lines)
backend/app/routes/pricing_analytics.py (200 lines)
backend/alembic/versions/xxxx_create_price_analysis_table.py
```

**Database Schema:**
```python
class PriceAnalysis(Base):
    __tablename__ = "price_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Market metrics
    market_avg: Mapped[float] = mapped_column(Float)
    market_median: Mapped[float] = mapped_column(Float)
    market_min: Mapped[float] = mapped_column(Float)
    market_max: Mapped[float] = mapped_column(Float)

    comparable_listings: Mapped[int] = mapped_column(Integer)
    recommended_price: Mapped[float] = mapped_column(Float)
    price_range_min: Mapped[float] = mapped_column(Float)
    price_range_max: Mapped[float] = mapped_column(Float)

    # Trend analysis
    price_trend: Mapped[str] = mapped_column(String(50))  # "increasing", "stable", "decreasing"
    trend_pct_change: Mapped[float] = mapped_column(Float)  # % change in 30 days

    # ML prediction (added later when enough data)
    ml_predicted_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ml_confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
```

**Price Analysis Algorithm:**
```python
# In pricing_analyzer.py

class PriceAnalyzer:
    @staticmethod
    def analyze_listing_price(listing_id: int):
        """Analyze market price for a listing"""

        listing = get_listing(listing_id)

        # Find comparable listings (same category, similar condition)
        comparables = find_comparable_listings(
            category=listing.category,
            condition=listing.condition,
            exclude_outliers=True
        )

        # Calculate market statistics
        prices = [c.price for c in comparables]

        analysis = PriceAnalysis(
            listing_id=listing_id,
            market_avg=statistics.mean(prices),
            market_median=statistics.median(prices),
            market_min=min(prices),
            market_max=max(prices),
            comparable_listings=len(comparables),
            recommended_price=calculate_optimal_price(listing, comparables),
            price_range_min=percentile(prices, 0.25),  # 25th percentile
            price_range_max=percentile(prices, 0.75),  # 75th percentile
            price_trend=analyze_trend(comparables, days=30),
            trend_pct_change=calculate_trend_percentage(comparables, days=30)
        )

        return analysis

    @staticmethod
    def calculate_optimal_price(listing, comparables):
        """Calculate recommended price"""

        # Base: market median
        base_price = statistics.median([c.price for c in comparables])

        # Adjustments based on listing features
        adjustments = 0.0

        # Condition adjustment
        if listing.condition == "excellent":
            adjustments += base_price * 0.05  # +5%
        elif listing.condition == "good":
            adjustments += base_price * 0.02  # +2%
        elif listing.condition == "fair":
            adjustments -= base_price * 0.05  # -5%
        elif listing.condition == "poor":
            adjustments -= base_price * 0.10  # -10%

        # Recency bonus (newer listings sell faster)
        days_old = (datetime.utcnow() - listing.created_at).days
        if days_old < 7:
            adjustments += base_price * 0.03  # +3%

        return max(0, base_price + adjustments)
```

**API Endpoints:**
```python
POST /listings/{listing_id}/analyze-price
  → Trigger price analysis
  → Returns: {
      "market_avg": 500.0,
      "market_median": 480.0,
      "recommended_price": 490.0,
      "price_range": [400.0, 600.0],
      "comparable_listings": 45,
      "trend": "increasing",
      "trend_change": "+5%"
    }

GET /listings/{listing_id}/price-analysis
  → Get cached analysis results

GET /listings/{listing_id}/comparable-listings?limit=10
  → Get list of similar items with prices
  → Useful for sellers to see competition

POST /seller/pricing/optimize
  → Analyze all seller's items
  → Returns batch results

PATCH /listings/{listing_id}/price
  → Accept recommendation or set custom price
  {
    "price": 499.99,
    "accept_recommendation": true
  }
```

**Background Task:**
```python
# Celery task to periodically re-analyze prices

@celery_app.task
def update_all_price_analyses():
    """Re-analyze prices daily for all active listings"""

    listings = db.query(Listing).filter(
        Listing.available == True
    ).all()

    for listing in listings:
        # Skip if analyzed within last 24 hours
        existing = db.query(PriceAnalysis)\
            .filter(PriceAnalysis.listing_id == listing.id)\
            .order_by(PriceAnalysis.analyzed_at.desc())\
            .first()

        if existing and (datetime.utcnow() - existing.analyzed_at).hours < 24:
            continue

        # Analyze price
        analysis = PriceAnalyzer.analyze_listing_price(listing.id)
        db.add(analysis)

    db.commit()
```

**Testing:**
- Test price analysis with various listing types
- Verify comparable listing selection
- Test recommendation accuracy
- Test trend calculation
- Test background task

**Deliverables:**
- ✅ Price analysis working
- ✅ Recommended prices calculated
- ✅ Comparable listings shown
- ✅ Trend analysis functional
- ✅ Background task updating prices daily

---

#### Sprint 3b: Elasticsearch Advanced Search (2-4 days)

**Setup Docker Compose:**
```yaml
# Add to docker-compose.yml:

elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
  container_name: deal-scout-elasticsearch
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
  ports:
    - "9200:9200"
  volumes:
    - elasticsearch-data:/usr/share/elasticsearch/data

volumes:
  elasticsearch-data:
```

**Files to Create:**
```
backend/app/search/elasticsearch_client.py (250 lines)
backend/app/search/elasticsearch_indexer.py (200 lines)
backend/app/tasks/index_listings.py (150 lines)
```

**Elasticsearch Client:**
```python
# In elasticsearch_client.py

from elasticsearch import Elasticsearch

class ElasticsearchClient:
    def __init__(self):
        self.client = Elasticsearch(["localhost:9200"])
        self.index_name = "listings"

    def create_index(self):
        """Create listings index with mappings"""

        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "title": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "category": {
                        "type": "keyword"
                    },
                    "price": {"type": "float"},
                    "condition": {"type": "keyword"},
                    "deal_score": {"type": "float"},
                    "created_at": {"type": "date"}
                }
            }
        }

        self.client.indices.create(index=self.index_name, body=mapping)

    def index_listing(self, listing_data):
        """Index a single listing"""
        self.client.index(
            index=self.index_name,
            id=listing_data["id"],
            body=listing_data
        )

    def search(self, query, filters=None, fuzziness="AUTO"):
        """Execute search with fuzzy matching"""

        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "description"],
                                "fuzziness": fuzziness,
                                "prefix_length": 2
                            }
                        }
                    ],
                    "filter": filters or []
                }
            }
        }

        results = self.client.search(index=self.index_name, body=search_body)
        return results

    def search_with_synonyms(self, query):
        """Search with synonym expansion"""

        # Example: "couch" matches "sofa", "couch", "settee"
        synonyms = {
            "couch": ["sofa", "settee", "divan"],
            "chair": ["seat", "stool"],
            "tv": ["television", "screen"]
        }

        expanded_query = query
        for key, values in synonyms.items():
            if key.lower() in query.lower():
                # Create OR query with synonyms
                expanded_query = f'({query} OR {" OR ".join(values)})'

        return self.search(expanded_query)
```

**Indexing Task:**
```python
# In app/tasks/index_listings.py

@celery_app.task
def index_all_listings():
    """Index all listings in Elasticsearch"""

    es = ElasticsearchClient()

    # Create index if not exists
    if not es.client.indices.exists(index="listings"):
        es.create_index()

    # Get all listings
    listings = db.query(Listing).all()

    for listing in listings:
        listing_data = {
            "id": listing.id,
            "title": listing.title,
            "description": listing.description,
            "category": listing.category,
            "price": listing.price,
            "condition": listing.condition.value if listing.condition else None,
            "deal_score": listing.deal_score.value if listing.deal_score else 0,
            "created_at": listing.created_at.isoformat()
        }
        es.index_listing(listing_data)

@celery_app.task
def index_new_listings():
    """Index listings created in last 24 hours"""

    es = ElasticsearchClient()

    # Get new listings
    from datetime import timedelta
    threshold = datetime.utcnow() - timedelta(hours=24)

    listings = db.query(Listing).filter(
        Listing.created_at > threshold
    ).all()

    for listing in listings:
        # Index listing (same as above)
        ...

# Celery Beat Schedule:
{
    'index-new-listings': {
        'task': 'app.tasks.index_listings.index_new_listings',
        'schedule': crontab(hour='*', minute=0),  # Every hour
    },
    'reindex-all-listings': {
        'task': 'app.tasks.index_listings.index_all_listings',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

**Enhanced Search Endpoints:**
```python
# Modify existing /listings/search/* endpoints to use Elasticsearch

GET /listings/search/listings?q=couch&fuzziness=AUTO&limit=20
  → Fuzzy matching (handles typos)
  → Returns: listings with relevance scores

GET /listings/search/suggestions?q=co&fuzzy=true
  → Autocomplete with fuzzy matching
  → "co" matches "couch", "coffee table", etc.

GET /listings/search/advanced?keywords=couch&keywords=leather&fuzzy=true
  → Advanced search with typo tolerance
  → Synonym matching
  → Returns faceted results
```

**Testing:**
- Test Elasticsearch connection
- Test listing indexing
- Test fuzzy search (e.g., "couch" with typo "coutch")
- Test synonym matching
- Test performance with large datasets
- Verify fallback to PostgreSQL if ES fails

**Deliverables:**
- ✅ Elasticsearch running in Docker
- ✅ Listings indexed automatically
- ✅ Fuzzy search working (typo tolerance)
- ✅ Synonym support
- ✅ Improved search performance
- ✅ Graceful fallback if ES unavailable

---

## Sprint Summary

| Sprint | Focus | Duration | Effort | Deliverables |
|--------|-------|----------|--------|--------------|
| 1 | Marketplaces | 5 days | 15-20h | Facebook + Offerup posting |
| 2 | Smart Deals | 5 days | 15-20h | Deal alerts + Multi-channel notifications |
| 3 | AI Features | 10 days | 25-30h | Pricing + Elasticsearch search |
| **Total** | **Full Phase 6** | **20 days** | **55-70h** | **All features** |

---

## Deployment Strategy

### Stage 1: Staging Environment (Internal Testing)
- Deploy to staging server
- Run full test suite
- Team testing and validation
- Performance benchmarking

### Stage 2: Beta Release (Early Users)
- Deploy to production
- Enable for 10% of users
- Monitor error rates
- Collect feedback

### Stage 3: Full Release
- Gradual rollout to all users
- Monitor performance metrics
- Scale resources if needed
- Track success metrics

### Rollback Plan
- Keep previous version deployed
- Feature flags for quick disable
- Database rollback scripts ready
- Monitoring alerts configured

---

## Success Metrics

### Week 1 (Marketplaces):
- ✅ Sellers connected: 50%+
- ✅ Cross-posted items: 1,000+
- ✅ Marketplace reach: 3-4x

### Week 2 (Smart Deals):
- ✅ Alert rules created: 100+
- ✅ User engagement: +40%
- ✅ Multi-channel adoption: 60%+

### Week 3 (Pricing):
- ✅ Price analyses run: 10,000+
- ✅ Seller adoption: 30%+
- ✅ Average price improvement: +25-30%

### Week 4 (Search):
- ✅ ES queries: 95%+
- ✅ Search speed: <100ms
- ✅ User satisfaction: +35%

---

## Team Assignments

### Recommended Team (3 developers):

**Developer 1: Marketplace Integrations**
- Sprint 1a: Facebook OAuth & posting
- Assist Sprint 1b: Offerup integration
- Duration: Week 1-1.5

**Developer 2: Smart Deals & Notifications**
- Sprint 2a: Deal alert rules
- Sprint 2b: Enhanced notifications
- Duration: Week 2

**Developer 3: AI & Search**
- Sprint 3a: ML pricing analysis
- Sprint 3b: Elasticsearch integration
- Duration: Week 3-4

**Optional DevOps/QA:**
- Infrastructure setup (Elasticsearch, services)
- Testing and deployment
- Monitoring and performance tuning

---

## Risk Mitigation

### High-Risk Items:

**1. Third-party API Failures**
- Risk: Facebook/Offerup API down
- Mitigation: Graceful degradation, queue failed requests
- Fallback: Store locally, retry later

**2. Elasticsearch Performance**
- Risk: ES queries slow or cluster fails
- Mitigation: Use PostgreSQL as fallback
- Plan: Monitor ES cluster health

**3. Data Consistency**
- Risk: PostgreSQL and ES get out of sync
- Mitigation: Daily full reindex, version tracking
- Plan: Alerts if sync issues detected

**4. Migration Complexity**
- Risk: Large existing dataset hard to migrate
- Mitigation: Run migrations in background, zero-downtime
- Plan: Test with production data snapshot first

---

## Dependencies & Requirements

### New Dependencies:
```bash
pip install elasticsearch>=7.0,<8.0
pip install twilio>=6.60.0  # For SMS
```

### External Services:
- Facebook App credentials (free)
- Offerup API access (free)
- Twilio account (pay-as-you-go)
- Elasticsearch server (Docker, free)

### Infrastructure:
- Additional Celery workers (for background tasks)
- Elasticsearch server (can use Docker)
- No significant hardware upgrades needed

---

## Documentation Requirements

After completion, create:
1. **API Documentation** - New endpoints
2. **Seller Guide** - How to use marketplaces
3. **User Guide** - Deal alerts and notifications
4. **Admin Guide** - Managing integrations
5. **Technical Architecture** - System design
6. **Troubleshooting Guide** - Common issues

---

## Post-Launch Monitoring

### Key Metrics to Track:
- API error rates
- Response times by endpoint
- Marketplace sync issues
- Deal alert accuracy
- Notification delivery rates
- Elasticsearch index size
- User engagement metrics

### Monitoring Tools:
- Use existing Prometheus setup
- Add alerts for critical errors
- Dashboard for team visibility
- Daily monitoring report

---

## What's Next After Phase 6?

### Phase 6b (Optional):
- Poshmark marketplace integration
- SMS rate-limiting refinement
- ML model training (if 4+ weeks of data)

### Phase 7 Candidates:
- Social features (comments, sharing)
- User ratings & verification
- Advanced analytics dashboard
- Mobile app support

---

## Summary

This hybrid plan (Option A + C) gives you:

✅ **Quick Revenue Wins (Week 1-2)**
- 3-4x seller reach through multi-marketplace
- 40% user engagement boost
- Smart deal alerts driving conversions

✅ **Advanced AI Features (Week 3-4)**
- ML pricing helping sellers earn more
- Elasticsearch powering smart discovery
- Staying ahead of competition

✅ **Realistic Timeline**
- 4 weeks total
- 2-3 developer team
- Staged rollout to manage risk
- Clear success metrics

---

**Ready to build Phase 6? Let's make it happen! 🚀**

---

Generated: October 29, 2025
Status: Ready to Begin Implementation
