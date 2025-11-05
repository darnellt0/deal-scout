# Deal Scout - Vertical Implementation Plan
**Multi-Agent Parallel Development Strategy**

**Generated:** 2025-11-05
**Status:** Ready for Parallel Execution
**Target Completion:** 3-4 weeks with 4-5 parallel agents

---

## Executive Summary

This plan divides the remaining features into **5 independent verticals** that can be developed simultaneously by separate agents. Each vertical is designed to minimize dependencies and conflicts.

### What Will Be Built

Based on Phase 6 and Phase 7 roadmaps, skipping already-implemented features:

**NOT building (already exists):**
- ✅ Facebook OAuth integration
- ✅ OfferUp OAuth integration
- ✅ Multi-marketplace posting
- ✅ Core authentication & user management
- ✅ Basic listing search and feed
- ✅ Seller Snap Studio (AI copywriter)
- ✅ Basic notifications (email, SMS, Discord, push)

**BUILDING (from suggestions):**
- 🔨 Vertical 1: Intelligent Deal Alerts & Rules Engine
- 🔨 Vertical 2: Advanced Notification System
- 🔨 Vertical 3: ML-Powered Pricing Engine
- 🔨 Vertical 4: Elasticsearch Advanced Search
- 🔨 Vertical 5: User Engagement Features

---

## Vertical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERTICAL 1: DEAL ALERTS                      │
│  Agent: deal-alerts-agent                                       │
│  Files: backend/app/routes/deal_alert_rules.py                 │
│         backend/app/tasks/check_deal_alerts.py                 │
│         backend/app/core/models/deal_alert_rule.py             │
│  DB: deal_alert_rules, watchlist_items                         │
│  Duration: 5-7 days                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              VERTICAL 2: NOTIFICATION SYSTEM                    │
│  Agent: notification-agent                                      │
│  Files: backend/app/routes/notification_preferences.py         │
│         backend/app/tasks/send_digest_emails.py                │
│         backend/app/core/email_templates/                      │
│  DB: notification_preferences (extended)                        │
│  Duration: 5-7 days                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                VERTICAL 3: ML PRICING ENGINE                    │
│  Agent: pricing-agent                                           │
│  Files: backend/app/ml/pricing_analyzer.py                     │
│         backend/app/ml/price_predictor.py                      │
│         backend/app/routes/pricing_analytics.py                │
│  DB: price_analysis                                             │
│  Duration: 7-10 days                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│           VERTICAL 4: ELASTICSEARCH SEARCH                      │
│  Agent: search-agent                                            │
│  Files: backend/app/search/elasticsearch_client.py             │
│         backend/app/search/elasticsearch_indexer.py            │
│         backend/app/tasks/index_listings.py                    │
│  Infrastructure: Elasticsearch Docker container                 │
│  Duration: 7-10 days                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│          VERTICAL 5: USER ENGAGEMENT FEATURES                   │
│  Agent: engagement-agent                                        │
│  Files: backend/app/routes/user_profile.py                     │
│         backend/app/routes/seller_analytics.py                 │
│         backend/app/core/file_service.py                       │
│  DB: user_ratings, user_verification                            │
│  Duration: 5-7 days                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## VERTICAL 1: Intelligent Deal Alerts & Rules Engine

**Agent ID:** `deal-alerts-agent`
**Priority:** HIGH (drives user engagement)
**Duration:** 5-7 days
**Effort:** 20-25 hours

### Scope

Implement custom deal alert rules that automatically notify users when matching listings appear.

### Features to Implement

1. **Deal Alert Rules CRUD**
   - Create, read, update, delete alert rules
   - Rule testing/preview functionality
   - Pause/resume functionality

2. **Rule Matching Engine**
   - Keyword matching (includes/excludes)
   - Price range filtering
   - Category filtering
   - Location-based filtering (radius)
   - Deal score threshold filtering
   - Condition filtering

3. **Watchlist & Price Drop Alerts**
   - Add listings to watchlist
   - Set price thresholds
   - Monitor price changes
   - Alert when price drops below threshold

4. **Background Tasks**
   - Check rules every 30 minutes
   - Check price drops every hour
   - Clean up old alerts weekly

### Database Schema

```sql
-- New table: deal_alert_rules
CREATE TABLE deal_alert_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT true,

    -- Matching criteria (JSON)
    keywords JSONB DEFAULT '[]'::jsonb,
    exclude_keywords JSONB DEFAULT '[]'::jsonb,
    categories JSONB DEFAULT '[]'::jsonb,
    condition VARCHAR(50),

    -- Price criteria
    min_price NUMERIC(10,2),
    max_price NUMERIC(10,2),

    -- Location criteria
    location VARCHAR(255),
    radius_mi INTEGER,

    -- Deal score
    min_deal_score NUMERIC(3,2),

    -- Notification settings
    notification_channels JSONB DEFAULT '["email"]'::jsonb,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_triggered_at TIMESTAMP,

    INDEX idx_user_enabled (user_id, enabled),
    INDEX idx_created_at (created_at)
);

-- New table: watchlist_items
CREATE TABLE watchlist_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    price_threshold NUMERIC(10,2),
    alert_sent BOOLEAN DEFAULT false,
    added_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, listing_id),
    INDEX idx_user_id (user_id),
    INDEX idx_listing_id (listing_id)
);
```

### API Endpoints

```python
# Deal Alert Rules
POST   /api/deal-alert-rules              # Create rule
GET    /api/deal-alert-rules              # List user's rules
GET    /api/deal-alert-rules/{rule_id}    # Get rule details
PATCH  /api/deal-alert-rules/{rule_id}    # Update rule
DELETE /api/deal-alert-rules/{rule_id}    # Delete rule
POST   /api/deal-alert-rules/{rule_id}/test    # Test rule
POST   /api/deal-alert-rules/{rule_id}/pause   # Pause rule
POST   /api/deal-alert-rules/{rule_id}/resume  # Resume rule

# Watchlist
POST   /api/watchlist/items               # Add to watchlist
GET    /api/watchlist                     # Get watchlist
DELETE /api/watchlist/items/{item_id}     # Remove from watchlist
PATCH  /api/watchlist/items/{item_id}     # Update price threshold
```

### Files to Create

```
backend/app/core/models/deal_alert_rule.py           (150 lines)
backend/app/core/models/watchlist_item.py            (80 lines)
backend/app/routes/deal_alert_rules.py               (350 lines)
backend/app/routes/watchlist.py                      (200 lines)
backend/app/tasks/check_deal_alerts.py               (300 lines)
backend/app/tasks/check_price_drops.py               (200 lines)
backend/alembic/versions/xxx_create_deal_alerts.py   (100 lines)

tests/test_deal_alert_rules.py                       (250 lines)
tests/test_watchlist.py                              (150 lines)
```

### Testing Requirements

- Unit tests for rule matching logic
- Integration tests for API endpoints
- Background task execution tests
- Price drop detection tests
- Rule preview functionality tests

### Success Metrics

- Users can create and manage alert rules
- Background task runs every 30 minutes
- Matching listings trigger notifications
- Price drops detected and alerted
- Test coverage >80%

---

## VERTICAL 2: Advanced Notification System

**Agent ID:** `notification-agent`
**Priority:** HIGH (works with Vertical 1)
**Duration:** 5-7 days
**Effort:** 18-22 hours

### Scope

Enhance the notification system with preferences, digest emails, quiet hours, and multi-channel support.

### Features to Implement

1. **Enhanced Notification Preferences**
   - Channel selection (email, SMS, Discord, push)
   - Frequency settings (immediate, daily digest, weekly digest)
   - Quiet hours configuration
   - Rate limiting (max notifications per day)
   - Category filters

2. **Digest Email System**
   - Daily digest emails (9 AM)
   - Weekly digest emails (Monday 9 AM)
   - Professional HTML templates
   - Deal cards with images
   - Personalized recommendations

3. **Smart Notification Routing**
   - Respect quiet hours
   - Enforce rate limits
   - Channel preference handling
   - Frequency aggregation

4. **Background Tasks**
   - Send daily digests
   - Send weekly digests
   - Cleanup old notifications

### Database Schema

```sql
-- Extend existing notification_preferences table
ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS
    email_enabled BOOLEAN DEFAULT true,
    push_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    discord_enabled BOOLEAN DEFAULT false,

    notification_frequency VARCHAR(50) DEFAULT 'immediate',

    quiet_hours_start TIME,
    quiet_hours_end TIME,

    max_notifications_per_day INTEGER DEFAULT 50,

    enabled_categories JSONB DEFAULT '[]'::jsonb;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_notification_frequency
    ON notification_preferences(notification_frequency);
```

### API Endpoints

```python
# Notification Preferences
GET    /api/notification-preferences                    # Get preferences
PATCH  /api/notification-preferences/channels          # Update channels
PATCH  /api/notification-preferences/frequency         # Update frequency
PATCH  /api/notification-preferences/quiet-hours       # Update quiet hours
PATCH  /api/notification-preferences/rate-limit        # Update rate limit
PATCH  /api/notification-preferences/categories        # Update categories
GET    /api/notification-preferences/summary           # Get summary

# Digest Management
GET    /api/notifications/digest/preview               # Preview digest
POST   /api/notifications/digest/test                  # Send test digest
```

### Files to Create/Modify

```
backend/app/routes/notification_preferences.py (expand +200 lines)
backend/app/core/notification_service.py              (300 lines)
backend/app/tasks/send_digest_emails.py               (400 lines)
backend/app/core/email_templates/digest.html          (250 lines)
backend/app/core/email_templates/digest_text.txt      (100 lines)
backend/alembic/versions/xxx_extend_notifications.py  (80 lines)

tests/test_notification_preferences.py                (200 lines)
tests/test_digest_emails.py                           (180 lines)
```

### Email Template Design

```html
<!-- Digest email structure -->
<!DOCTYPE html>
<html>
<head>
  <style>
    /* Professional email styling */
    /* Deal cards */
    /* Price highlights */
    /* CTA buttons */
  </style>
</head>
<body>
  <div class="container">
    <h1>Your Daily Deal Digest</h1>
    <p>Hi {{ user.name }}, here are {{ deal_count }} deals matching your preferences:</p>

    {% for deal in deals %}
    <div class="deal-card">
      <img src="{{ deal.image_url }}" alt="{{ deal.title }}">
      <h3>{{ deal.title }}</h3>
      <p class="price">${{ deal.price }}</p>
      <span class="deal-score">Deal Score: {{ deal.score }}</span>
      <a href="{{ deal.url }}" class="btn">View Deal</a>
    </div>
    {% endfor %}

    <div class="footer">
      <a href="{{ preferences_url }}">Manage Preferences</a>
    </div>
  </div>
</body>
</html>
```

### Celery Task Schedule

```python
{
    'send-daily-digest-emails': {
        'task': 'app.tasks.send_digest_emails.send_daily_digests',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
    'send-weekly-digest-emails': {
        'task': 'app.tasks.send_digest_emails.send_weekly_digests',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),  # Monday 9 AM
    },
    'cleanup-old-notifications': {
        'task': 'app.tasks.cleanup.cleanup_old_notifications',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Sunday 2 AM
    },
}
```

### Testing Requirements

- Test all notification channel preferences
- Test quiet hours enforcement
- Test rate limiting
- Test digest email generation
- Test HTML/text email rendering
- Test frequency aggregation

### Success Metrics

- Users can configure notification preferences
- Digest emails sent on schedule
- Quiet hours respected
- Rate limits enforced
- Test coverage >75%

---

## VERTICAL 3: ML-Powered Pricing Engine

**Agent ID:** `pricing-agent`
**Priority:** MEDIUM (valuable seller feature)
**Duration:** 7-10 days
**Effort:** 30-35 hours

### Scope

Build an intelligent pricing recommendation system using market analysis and ML predictions.

### Features to Implement

1. **Price Analysis Engine**
   - Find comparable listings
   - Calculate market statistics (avg, median, min, max)
   - Identify pricing anomalies
   - Suggest optimal price range
   - Condition-based adjustments

2. **Trend Analysis**
   - Track price trends over time
   - Calculate percentage changes
   - Identify seasonal patterns
   - Predict market direction

3. **Price Predictor (ML)**
   - Feature engineering from listing data
   - Train on historical sales data
   - Predict optimal selling price
   - Confidence scoring

4. **Background Tasks**
   - Daily price analysis refresh
   - Weekly trend calculation
   - Monthly model retraining

### Database Schema

```sql
-- New table: price_analysis
CREATE TABLE price_analysis (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    analyzed_at TIMESTAMP DEFAULT NOW(),

    -- Market metrics
    market_avg NUMERIC(10,2),
    market_median NUMERIC(10,2),
    market_min NUMERIC(10,2),
    market_max NUMERIC(10,2),

    comparable_listings INTEGER,
    recommended_price NUMERIC(10,2),
    price_range_min NUMERIC(10,2),
    price_range_max NUMERIC(10,2),

    -- Trend analysis
    price_trend VARCHAR(50),  -- 'increasing', 'stable', 'decreasing'
    trend_pct_change NUMERIC(5,2),

    -- ML predictions (optional, added when trained)
    ml_predicted_price NUMERIC(10,2),
    ml_confidence_score NUMERIC(3,2),

    INDEX idx_listing_id (listing_id),
    INDEX idx_analyzed_at (analyzed_at)
);

-- Track price history
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    price NUMERIC(10,2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_listing_id (listing_id),
    INDEX idx_recorded_at (recorded_at)
);
```

### API Endpoints

```python
# Price Analysis
POST   /api/listings/{listing_id}/analyze-price        # Trigger analysis
GET    /api/listings/{listing_id}/price-analysis       # Get cached analysis
GET    /api/listings/{listing_id}/comparable-listings  # Get comparables
GET    /api/listings/{listing_id}/price-history        # Get price history

# Batch Operations
POST   /api/seller/pricing/optimize                    # Analyze all seller items
POST   /api/seller/pricing/batch-analyze               # Batch analysis

# Analytics
GET    /api/pricing/market-trends                      # Market trend data
GET    /api/pricing/category-stats/{category}          # Category statistics
```

### Files to Create

```
backend/app/ml/pricing_analyzer.py                    (400 lines)
backend/app/ml/price_predictor.py                     (350 lines)
backend/app/ml/feature_engineering.py                 (200 lines)
backend/app/routes/pricing_analytics.py               (350 lines)
backend/app/tasks/update_price_analyses.py            (250 lines)
backend/app/core/models/price_analysis.py             (120 lines)
backend/alembic/versions/xxx_create_price_analysis.py (120 lines)

# ML model files
backend/app/ml/models/price_model.pkl                 (binary)
backend/app/ml/training/train_price_model.py          (300 lines)

tests/test_pricing_analyzer.py                        (250 lines)
tests/test_price_predictor.py                         (200 lines)
```

### Algorithm Design

```python
# Pricing analyzer logic
class PriceAnalyzer:
    def analyze_listing_price(self, listing_id: int) -> PriceAnalysis:
        """
        1. Get listing details
        2. Find comparable listings (same category, similar condition)
        3. Calculate market statistics
        4. Apply condition adjustments
        5. Factor in recency bonus
        6. Generate recommendation
        """

        listing = self.get_listing(listing_id)
        comparables = self.find_comparables(listing)

        # Market stats
        prices = [c.price for c in comparables]
        market_avg = statistics.mean(prices)
        market_median = statistics.median(prices)

        # Base price from median
        base_price = market_median

        # Adjustments
        condition_adjustment = self.calculate_condition_adjustment(listing.condition)
        recency_bonus = self.calculate_recency_bonus(listing.created_at)

        recommended_price = base_price * (1 + condition_adjustment + recency_bonus)

        return PriceAnalysis(
            listing_id=listing_id,
            market_avg=market_avg,
            market_median=market_median,
            recommended_price=recommended_price,
            # ... more fields
        )
```

### ML Model Features

```python
# Feature engineering for ML pricing
features = {
    # Item features
    'category_encoded': category_encoder.transform([listing.category]),
    'condition_score': condition_to_numeric(listing.condition),
    'age_days': (now - listing.created_at).days,
    'description_length': len(listing.description),
    'has_image': 1 if listing.image_url else 0,

    # Market features
    'market_avg_price': market_avg,
    'market_volume': comparable_count,
    'category_popularity': category_stats.popularity_score,

    # Temporal features
    'day_of_week': listing.created_at.weekday(),
    'month': listing.created_at.month,
    'is_weekend': 1 if listing.created_at.weekday() >= 5 else 0,
}

# Train model (when enough data available)
model = GradientBoostingRegressor(n_estimators=100)
model.fit(X_train, y_train)
```

### Testing Requirements

- Unit tests for price calculations
- Integration tests for API endpoints
- Test comparable listing selection
- Test condition adjustments
- Test trend calculations
- Test ML model predictions (when available)

### Success Metrics

- Price analysis completes in <2 seconds
- Recommendations within 10% of actual sale price
- Comparable listings relevant
- Background tasks run successfully
- Test coverage >75%

---

## VERTICAL 4: Elasticsearch Advanced Search

**Agent ID:** `search-agent`
**Priority:** MEDIUM (improves user experience)
**Duration:** 7-10 days
**Effort:** 28-32 hours

### Scope

Replace PostgreSQL full-text search with Elasticsearch for better performance, fuzzy matching, and advanced features.

### Features to Implement

1. **Elasticsearch Integration**
   - Docker container setup
   - Index creation and mapping
   - Connection management
   - Health monitoring

2. **Search Capabilities**
   - Full-text search with relevance scoring
   - Fuzzy matching (typo tolerance)
   - Synonym expansion
   - Faceted search
   - Autocomplete/suggestions
   - Search highlighting

3. **Indexing System**
   - Initial bulk indexing
   - Incremental indexing
   - Real-time updates
   - Reindexing strategies

4. **Background Tasks**
   - Hourly incremental indexing
   - Daily full reindex
   - Index optimization

### Infrastructure

```yaml
# Add to docker-compose.yml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
  container_name: deal-scout-elasticsearch
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
  ports:
    - "9200:9200"
    - "9300:9300"
  volumes:
    - elasticsearch-data:/usr/share/elasticsearch/data
  networks:
    - deal-scout-network
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 5

volumes:
  elasticsearch-data:
    driver: local
```

### Index Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "integer" },
      "title": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": { "type": "keyword" },
          "suggest": {
            "type": "completion",
            "analyzer": "simple"
          }
        }
      },
      "description": {
        "type": "text",
        "analyzer": "english"
      },
      "category": {
        "type": "keyword"
      },
      "price": {
        "type": "float"
      },
      "condition": {
        "type": "keyword"
      },
      "deal_score": {
        "type": "float"
      },
      "location": {
        "type": "geo_point"
      },
      "created_at": {
        "type": "date"
      },
      "marketplace": {
        "type": "keyword"
      }
    }
  },
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
      "analyzer": {
        "autocomplete": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "autocomplete_filter"]
        }
      },
      "filter": {
        "autocomplete_filter": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 20
        }
      }
    }
  }
}
```

### API Endpoints

```python
# Enhanced Search
GET    /api/search/listings                    # Main search (Elasticsearch)
GET    /api/search/suggestions                 # Autocomplete
GET    /api/search/advanced                    # Advanced search
GET    /api/search/facets                      # Get facets/aggregations

# Admin/Management
POST   /api/admin/search/reindex               # Trigger reindex
GET    /api/admin/search/status                # Index status
DELETE /api/admin/search/index                 # Delete index
POST   /api/admin/search/optimize              # Optimize index
```

### Files to Create

```
backend/app/search/elasticsearch_client.py            (350 lines)
backend/app/search/elasticsearch_indexer.py           (300 lines)
backend/app/search/query_builder.py                   (250 lines)
backend/app/tasks/index_listings.py                   (300 lines)
backend/app/routes/search.py (modify, +150 lines)
backend/app/core/config.py (add ES settings, +20 lines)

# Synonym dictionary
backend/app/search/synonyms.txt                       (200 lines)

tests/test_elasticsearch_search.py                    (300 lines)
tests/test_indexing.py                                (200 lines)
```

### Search Implementation

```python
# Elasticsearch client
class ElasticsearchClient:
    def __init__(self):
        self.client = Elasticsearch([settings.elasticsearch_url])
        self.index_name = "listings"

    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        fuzziness: str = "AUTO",
        size: int = 20,
        from_: int = 0
    ) -> Dict:
        """Execute fuzzy search with filters"""

        # Build multi-match query
        search_query = {
            "multi_match": {
                "query": query,
                "fields": ["title^3", "description"],
                "fuzziness": fuzziness,
                "prefix_length": 2,
                "type": "best_fields"
            }
        }

        # Build filter clauses
        filter_clauses = []
        if filters:
            if "category" in filters:
                filter_clauses.append({"term": {"category": filters["category"]}})
            if "min_price" in filters:
                filter_clauses.append({"range": {"price": {"gte": filters["min_price"]}}})
            if "max_price" in filters:
                filter_clauses.append({"range": {"price": {"lte": filters["max_price"]}}})

        # Complete query
        body = {
            "query": {
                "bool": {
                    "must": [search_query],
                    "filter": filter_clauses
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "description": {}
                }
            },
            "size": size,
            "from": from_
        }

        # Execute search
        response = self.client.search(index=self.index_name, body=body)
        return response

    def autocomplete(self, query: str, size: int = 10) -> List[str]:
        """Get autocomplete suggestions"""

        body = {
            "suggest": {
                "listing-suggest": {
                    "prefix": query,
                    "completion": {
                        "field": "title.suggest",
                        "size": size,
                        "skip_duplicates": True
                    }
                }
            }
        }

        response = self.client.search(index=self.index_name, body=body)
        suggestions = response["suggest"]["listing-suggest"][0]["options"]
        return [s["text"] for s in suggestions]
```

### Indexing Strategy

```python
# Celery tasks for indexing
@celery_app.task
def index_all_listings():
    """Full reindex - run daily at 2 AM"""

    es = ElasticsearchClient()

    # Delete and recreate index
    if es.client.indices.exists(index="listings"):
        es.client.indices.delete(index="listings")

    es.create_index()

    # Bulk index all listings
    listings = db.query(Listing).all()

    bulk_data = []
    for listing in listings:
        bulk_data.append({
            "index": {
                "_index": "listings",
                "_id": listing.id
            }
        })
        bulk_data.append(listing_to_doc(listing))

        # Batch every 1000 records
        if len(bulk_data) >= 2000:
            es.client.bulk(body=bulk_data)
            bulk_data = []

    # Index remaining
    if bulk_data:
        es.client.bulk(body=bulk_data)

@celery_app.task
def index_new_listings():
    """Incremental indexing - run hourly"""

    es = ElasticsearchClient()

    # Get listings created/updated in last hour
    threshold = datetime.utcnow() - timedelta(hours=1)
    listings = db.query(Listing).filter(
        or_(
            Listing.created_at > threshold,
            Listing.updated_at > threshold
        )
    ).all()

    for listing in listings:
        doc = listing_to_doc(listing)
        es.client.index(index="listings", id=listing.id, body=doc)
```

### Testing Requirements

- Test Elasticsearch connection
- Test search with various queries
- Test fuzzy matching (typos)
- Test autocomplete
- Test faceted search
- Test indexing (bulk and incremental)
- Test fallback to PostgreSQL if ES down
- Load testing with 10k+ queries

### Success Metrics

- Search queries <100ms average
- 95%+ queries use Elasticsearch
- Fuzzy matching handles typos
- Autocomplete suggestions relevant
- Index stays in sync with database
- Graceful fallback if ES unavailable
- Test coverage >70%

---

## VERTICAL 5: User Engagement Features

**Agent ID:** `engagement-agent`
**Priority:** LOW-MEDIUM (nice-to-have features)
**Duration:** 5-7 days
**Effort:** 22-26 hours

### Scope

Build user profile enhancements, ratings/reviews, and seller analytics to increase engagement.

### Features to Implement

1. **Enhanced User Profiles**
   - Avatar upload and management
   - Profile picture thumbnails
   - Bio and description
   - Social links

2. **User Ratings & Reviews**
   - Rate other users (1-5 stars)
   - Leave reviews
   - View rating history
   - Calculate average ratings

3. **User Verification**
   - Email verification (already exists)
   - Phone verification (SMS OTP)
   - Verification badges

4. **Seller Analytics Dashboard**
   - Total listings (active/sold)
   - Revenue over time
   - Most popular categories
   - Seller rating trends
   - Performance metrics

### Database Schema

```sql
-- Extend users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS
    avatar_url VARCHAR(500),
    avatar_uploaded_at TIMESTAMP,
    bio TEXT,
    location VARCHAR(255),
    verification_status VARCHAR(50) DEFAULT 'email_verified',
    phone_verified BOOLEAN DEFAULT false;

-- New table: user_ratings
CREATE TABLE user_ratings (
    id SERIAL PRIMARY KEY,
    from_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    rating NUMERIC(2,1) CHECK (rating >= 1.0 AND rating <= 5.0),
    review_text TEXT,

    context VARCHAR(50),  -- 'buyer', 'seller', 'transaction'
    transaction_id INTEGER,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(from_user_id, to_user_id, transaction_id),
    INDEX idx_to_user (to_user_id),
    INDEX idx_rating (rating)
);

-- New table: phone_verifications
CREATE TABLE phone_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    verified BOOLEAN DEFAULT false,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user_id (user_id),
    INDEX idx_phone (phone_number)
);
```

### API Endpoints

```python
# User Profile
GET    /api/users/me/profile                   # Get own profile
PATCH  /api/users/me/profile                   # Update profile
POST   /api/users/me/avatar                    # Upload avatar
DELETE /api/users/me/avatar                    # Delete avatar
GET    /api/users/{user_id}/profile            # Get public profile

# Ratings & Reviews
POST   /api/users/{user_id}/ratings            # Leave rating
GET    /api/users/{user_id}/ratings            # Get user's ratings
GET    /api/users/{user_id}/rating-summary     # Get average & count
GET    /api/users/me/ratings/given             # Ratings I gave

# Phone Verification
POST   /api/users/verify/phone                 # Request verification
POST   /api/users/verify/phone/confirm         # Confirm OTP

# Seller Analytics
GET    /api/seller/analytics/summary           # Key metrics
GET    /api/seller/analytics/listings          # Listing stats
GET    /api/seller/analytics/revenue           # Revenue over time
GET    /api/seller/analytics/categories        # Category breakdown
GET    /api/seller/analytics/trends            # Trends & insights
```

### Files to Create

```
backend/app/routes/user_profile.py                    (300 lines)
backend/app/routes/user_ratings.py                    (250 lines)
backend/app/routes/seller_analytics.py                (400 lines)
backend/app/core/file_service.py                      (200 lines)
backend/app/core/verification_service.py              (250 lines)
backend/app/core/models/user_rating.py                (100 lines)
backend/alembic/versions/xxx_user_enhancements.py     (150 lines)

tests/test_user_profile.py                            (200 lines)
tests/test_user_ratings.py                            (180 lines)
tests/test_seller_analytics.py                        (220 lines)
```

### Avatar Upload Implementation

```python
# File service for avatar uploads
class FileService:
    def __init__(self):
        self.storage_path = settings.static_files_path / "avatars"
        self.storage_path.mkdir(exist_ok=True)

    def upload_avatar(self, user_id: int, image_file: UploadFile) -> str:
        """
        Upload and process avatar image
        1. Validate file type and size
        2. Generate unique filename
        3. Resize to 200x200
        4. Save as WebP
        5. Return URL
        """

        # Validate
        if image_file.content_type not in ["image/jpeg", "image/png"]:
            raise ValueError("Invalid image type")

        # Read image
        image = Image.open(image_file.file)

        # Resize to 200x200
        image = image.resize((200, 200), Image.LANCZOS)

        # Convert to WebP
        filename = f"{user_id}_{uuid.uuid4().hex}.webp"
        filepath = self.storage_path / filename
        image.save(filepath, "WEBP", quality=85)

        # Return URL
        return f"/static/avatars/{filename}"
```

### Seller Analytics Implementation

```python
# Seller analytics service
class SellerAnalytics:
    def get_summary(self, user_id: int) -> Dict:
        """Get seller metrics summary"""

        # Get all seller's items
        items = db.query(MyItem).filter(MyItem.user_id == user_id).all()

        # Calculate metrics
        total_listings = len(items)
        active_listings = len([i for i in items if i.status == "active"])
        sold_listings = len([i for i in items if i.status == "sold"])

        # Revenue
        total_revenue = sum(i.price for i in items if i.status == "sold")

        # Average rating
        avg_rating = db.query(func.avg(UserRating.rating)).filter(
            UserRating.to_user_id == user_id
        ).scalar() or 0.0

        return {
            "total_listings": total_listings,
            "active_listings": active_listings,
            "sold_listings": sold_listings,
            "total_revenue": float(total_revenue),
            "average_rating": float(avg_rating),
            "rating_count": db.query(UserRating).filter(
                UserRating.to_user_id == user_id
            ).count()
        }

    def get_revenue_over_time(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get daily revenue for past N days"""

        cutoff = datetime.utcnow() - timedelta(days=days)

        results = db.query(
            func.date(Order.completed_at).label("date"),
            func.sum(Order.price).label("revenue")
        ).join(
            CrossPost, Order.cross_post_id == CrossPost.id
        ).join(
            MyItem, CrossPost.my_item_id == MyItem.id
        ).filter(
            MyItem.user_id == user_id,
            Order.status == "completed",
            Order.completed_at >= cutoff
        ).group_by(
            func.date(Order.completed_at)
        ).all()

        return [
            {"date": str(r.date), "revenue": float(r.revenue)}
            for r in results
        ]
```

### Testing Requirements

- Test avatar upload and resizing
- Test profile updates
- Test rating creation and retrieval
- Test phone verification flow
- Test analytics calculations
- Test revenue aggregations

### Success Metrics

- Users can upload avatars
- Avatars resized and optimized
- Rating system functional
- Phone verification working
- Analytics accurate
- Test coverage >75%

---

## Integration Points & Dependencies

### Vertical Dependencies

```
Vertical 1 (Deal Alerts) ──┐
                           ├──> Vertical 2 (Notifications)
                           │    (Deal alerts trigger notifications)
                           │
Vertical 3 (Pricing) ──────┘
(Price drops can trigger alerts)

Vertical 4 (Search) ────────> Independent
                               (Can use PostgreSQL fallback)

Vertical 5 (Engagement) ────> Independent
                               (Separate feature set)
```

### Shared Resources

All verticals share:
- Database (PostgreSQL)
- Redis (Celery)
- Celery worker pool
- FastAPI application

**Migration Strategy:**
- Each vertical creates its own Alembic migration
- Migrations numbered sequentially
- Can be run independently

### Configuration

```python
# Add to backend/app/core/config.py

class Settings:
    # ... existing settings ...

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index_prefix: str = "deal-scout"

    # File storage
    static_files_path: Path = Path("/app/static")
    max_avatar_size_mb: int = 5

    # Twilio (already exists)
    # twilio_account_sid: str
    # twilio_auth_token: str
    # twilio_phone_number: str
```

---

## Execution Strategy

### Week 1-2: Parallel Development

```
Agent 1 (deal-alerts-agent):
  ├─ Days 1-2: Database schema + models
  ├─ Days 3-4: API endpoints (CRUD)
  ├─ Days 5-6: Rule matching logic
  └─ Days 7-8: Background tasks + testing

Agent 2 (notification-agent):
  ├─ Days 1-2: Extend notification preferences
  ├─ Days 3-4: Email templates
  ├─ Days 5-6: Digest email logic
  └─ Days 7-8: Background tasks + testing

Agent 3 (pricing-agent):
  ├─ Days 1-3: Database schema + price analyzer
  ├─ Days 4-6: Comparable finding + recommendations
  ├─ Days 7-8: API endpoints
  └─ Days 9-10: Background tasks + testing

Agent 4 (search-agent):
  ├─ Days 1-2: Elasticsearch setup
  ├─ Days 3-4: Index mapping + client
  ├─ Days 5-6: Search implementation
  ├─ Days 7-8: Indexing tasks
  └─ Days 9-10: Testing + optimization

Agent 5 (engagement-agent):
  ├─ Days 1-2: Database schema + file service
  ├─ Days 3-4: User profile endpoints
  ├─ Days 5-6: Ratings + verification
  └─ Days 7-8: Analytics + testing
```

### Week 3: Integration & Testing

```
All Agents:
  ├─ Integration testing
  ├─ Fix cross-vertical bugs
  ├─ Performance optimization
  ├─ Documentation updates
  └─ Code review
```

### Week 4: Deployment

```
DevOps:
  ├─ Deploy to staging
  ├─ Run full test suite
  ├─ Load testing
  ├─ Security review
  └─ Production deployment
```

---

## Testing Strategy

### Unit Tests (Per Vertical)

Each agent writes unit tests for:
- Database models
- Business logic
- API endpoints
- Background tasks

**Target:** 75%+ coverage per vertical

### Integration Tests

Test cross-vertical functionality:
- Deal alerts → Notifications
- Price drops → Alerts → Notifications
- Search → Listings → Pricing

### End-to-End Tests

User workflows:
1. Create deal alert → Receive notification
2. Upload item → Get price recommendation
3. Search with typo → Find results
4. Upload avatar → View profile

### Performance Tests

- Elasticsearch: 10k queries/second
- Price analysis: <2 seconds per listing
- Rule matching: <5 seconds for 1000 rules
- Digest emails: 10k users in <10 minutes

---

## Deployment Plan

### Phase 1: Staging Deployment

```bash
# Deploy each vertical to staging
git checkout main
git pull origin main

# Merge vertical branches
git merge vertical-1-deal-alerts
git merge vertical-2-notifications
git merge vertical-3-pricing
git merge vertical-4-search
git merge vertical-5-engagement

# Run migrations
docker-compose exec backend alembic upgrade head

# Restart services
docker-compose restart backend worker beat

# Run tests
docker-compose exec backend pytest
```

### Phase 2: Feature Flags

Enable features gradually:

```python
# Feature flags
DEAL_ALERTS_ENABLED = True
DIGEST_EMAILS_ENABLED = True
ML_PRICING_ENABLED = True
ELASTICSEARCH_ENABLED = False  # Enable after testing
USER_RATINGS_ENABLED = True
```

### Phase 3: Production Rollout

```
Day 1:   Deploy infrastructure (Elasticsearch)
Day 2-3: Deploy code, run migrations
Day 4:   Enable Vertical 1 (10% users)
Day 5:   Enable Vertical 2 (10% users)
Day 6:   Enable Vertical 3 (10% users)
Day 7:   Enable Vertical 4 (25% users)
Day 8:   Enable Vertical 5 (25% users)
Day 9:   Increase to 50% users
Day 10:  Full rollout (100% users)
```

### Rollback Plan

Each vertical can be disabled independently:

```python
# Disable feature if issues
DEAL_ALERTS_ENABLED = False  # Disables Vertical 1

# Database rollback
alembic downgrade -1
```

---

## Success Metrics

### Overall Goals

By end of implementation (4 weeks):

**User Engagement:**
- 🎯 40% increase in daily active users
- 🎯 65% user retention (up from 40%)
- 🎯 3x session duration

**Deal Discovery:**
- 🎯 100+ active alert rules created
- 🎯 5% deal click rate (up from 2%)
- 🎯 150% improvement in conversion rate

**Search Performance:**
- 🎯 95% queries via Elasticsearch
- 🎯 <100ms average search time
- 🎯 Typo tolerance working

**Pricing Accuracy:**
- 🎯 10k+ price analyses run
- 🎯 Recommendations within 10% of sale price
- 🎯 30% seller adoption rate

**User Satisfaction:**
- 🎯 75% email open rate for digests
- 🎯 4.5+ star average user rating
- 🎯 50% avatar upload rate

---

## Resource Requirements

### Team

- **5 Agents** (Claude Code instances)
- **1 DevOps/QA** (optional, for deployment)
- **1 Project Manager** (coordination)

### Infrastructure

**Development:**
- Existing: PostgreSQL, Redis, Docker
- New: Elasticsearch (1 node, 2GB RAM)

**Production:**
- Elasticsearch cluster (3 nodes, 8GB RAM each)
- Additional Celery workers (2-3 workers)
- S3 bucket for avatars (optional, can use local storage)

### External Services

- Twilio: Already configured
- Discord: Webhooks (free)
- Email: Existing SMTP setup
- Elasticsearch: Self-hosted

### Timeline

- **Week 1-2:** Parallel development
- **Week 3:** Integration & testing
- **Week 4:** Deployment & monitoring

**Total Duration:** 4 weeks (20 working days)

---

## Risk Mitigation

### High-Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| Elasticsearch downtime | High | Fallback to PostgreSQL search |
| Notification spam | High | Rate limiting + quiet hours |
| Price analysis errors | Medium | Human review before publishing |
| Merge conflicts | Medium | Clear file ownership per vertical |
| Performance degradation | Medium | Load testing before production |

### Contingency Plans

**If Vertical 1 (Alerts) delayed:**
- Can launch Vertical 2 (Notifications) independently
- Deal alerts not required for other features

**If Vertical 4 (Search) delayed:**
- Continue using PostgreSQL search
- Deploy ES later as enhancement

**If Vertical 5 (Engagement) delayed:**
- Can skip for initial launch
- Add later as enhancement

---

## Next Steps

### Immediate Actions

1. **Review this plan** with stakeholders
2. **Create feature branches** for each vertical:
   ```bash
   git checkout -b vertical-1-deal-alerts
   git checkout -b vertical-2-notifications
   git checkout -b vertical-3-pricing
   git checkout -b vertical-4-search
   git checkout -b vertical-5-engagement
   ```

3. **Setup development environment**
   - Install Elasticsearch locally
   - Configure Twilio credentials
   - Setup test data

4. **Assign agents to verticals**
   - Agent 1 → Deal Alerts
   - Agent 2 → Notifications
   - Agent 3 → Pricing
   - Agent 4 → Search
   - Agent 5 → Engagement

5. **Kick off development** (Week 1)

---

## Documentation Requirements

Each agent should create:

1. **API Documentation** (OpenAPI/Swagger)
   - Endpoint descriptions
   - Request/response schemas
   - Example calls

2. **Database Documentation**
   - Schema diagrams
   - Migration notes
   - Index rationale

3. **User Guides**
   - Feature walkthroughs
   - Screenshots (if UI changes)
   - Best practices

4. **Technical Documentation**
   - Architecture decisions
   - Algorithm explanations
   - Performance considerations

---

## Summary

This vertical implementation plan provides:

✅ **5 independent work streams** that can run in parallel
✅ **Clear ownership** - each agent has distinct files/features
✅ **Minimal conflicts** - separate database tables, routes, tasks
✅ **Incremental value** - each vertical delivers standalone features
✅ **4-week timeline** with parallel execution
✅ **Clear success metrics** for each vertical
✅ **Risk mitigation** strategies
✅ **Detailed technical specifications**

**Ready to begin?** Each vertical has:
- Database schema
- API endpoints
- File list
- Implementation details
- Testing requirements
- Success criteria

Each agent can start immediately on their assigned vertical!

---

**Document Version:** 1.0
**Last Updated:** 2025-11-05
**Status:** Ready for Execution 🚀
