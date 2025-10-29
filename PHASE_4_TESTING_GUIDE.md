# Phase 4 Testing Guide

This guide covers how to test all Phase 4 endpoints (Buyer, Seller, Marketplace Accounts, Notifications, and Pricing).

## Quick Start

### Prerequisites
- Backend running on `http://localhost:8000`
- Docker Compose services up and running
- A REST client (curl, Postman, or similar)

### Verify Backend is Running
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "ok": true,
  "db": true,
  "redis": true,
  "queue_depth": 0,
  "version": "0.1.0",
  "time": "2025-10-29T..."
}
```

---

## Step-by-Step Testing Flow

### **STEP 1: Authentication (Required for all tests)**

#### 1a. Register a Test User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testbuyer",
    "email": "buyer@example.com",
    "password": "TestPassword123",
    "first_name": "Test",
    "last_name": "Buyer"
  }'
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testbuyer",
    "email": "buyer@example.com",
    "role": "buyer",
    "is_active": true,
    "is_verified": false
  }
}
```

**Save the `access_token`** - You'll need this for authenticated requests!

#### 1b. Register a Seller User (for seller tests)
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testseller",
    "email": "seller@example.com",
    "password": "TestPassword123",
    "first_name": "Test",
    "last_name": "Seller"
  }'
```

**Save this seller's access token too!**

#### 1c. Promote Seller to Seller Role (Admin-only - optional)
For now, we can test with the default "buyer" role. To make them a true seller in production:
```bash
# This would require an admin endpoint - not yet implemented
# For testing, the "require_seller" check allows admin OR seller role
# So a buyer will return 403 on seller endpoints
```

**Alternative**: Create a user that will be your test seller.

---

### **STEP 2: Test Buyer Endpoints**

Use the buyer's access token from Step 1a.

#### 2a. List Available Deals
```bash
curl -X GET "http://localhost:8000/buyer/deals?limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Query Parameters**:
- `limit` (1-50, default: 10)
- `category` (optional, filters by category like "couch")
- `min_score` (optional, minimum deal score)
- `max_price` (optional, maximum price)
- `condition` (optional, like "good", "excellent")

**Expected Response**:
```json
[
  {
    "id": 1,
    "title": "Nice Couch",
    "price": 150.0,
    "condition": "good",
    "category": "furniture>sofas",
    "url": "https://example.com/item/123",
    "thumbnail_url": "https://example.com/img/123.jpg",
    "deal_score": 8.5,
    "auto_message": "Hey, interested in...",
    "price_cents": 15000,
    "location": {"coords": [37.77, -122.41]},
    "created_at": "2025-10-29T..."
  }
]
```

**Testing Tip**: If you see no deals, you may need to seed test data first (see **Seed Test Data** section below).

#### 2b. Get Buyer Preferences
```bash
curl -X GET "http://localhost:8000/buyer/preferences" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response**:
```json
{
  "user_id": 1,
  "max_price_couch": 1000,
  "max_price_island": 2000,
  "location": null,
  "search_radius_mi": 50,
  "notification_enabled": true,
  "notification_channels": ["email"]
}
```

#### 2c. Update Buyer Preferences
```bash
curl -X PUT "http://localhost:8000/buyer/preferences?max_price_couch=800&search_radius_mi=25&notification_enabled=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response**:
```json
{
  "message": "Preferences updated successfully"
}
```

#### 2d. Save a Deal to Watch List
First, get a deal ID from Step 2a, then:
```bash
curl -X POST "http://localhost:8000/buyer/deals/1/save" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response**:
```json
{
  "message": "Deal saved successfully"
}
```

#### 2e. Get Saved Deals
```bash
curl -X GET "http://localhost:8000/buyer/deals/saved" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response**:
```json
[
  {
    "id": 1,
    "title": "Nice Couch",
    "price": 150.0,
    "condition": "good",
    "url": "https://example.com/item/123",
    "deal_score": 8.5
  }
]
```

#### 2f. List Notifications
```bash
curl -X GET "http://localhost:8000/buyer/notifications?limit=20&status_filter=unread" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Query Parameters**:
- `limit` (1-100, default: 20)
- `status_filter` (optional, "read" or "unread")

**Expected Response**:
```json
[
  {
    "id": 1,
    "channel": "email",
    "status": "unread",
    "payload": {"deal_title": "Free Couch", "score": 10},
    "sent_at": "2025-10-29T...",
    "created_at": "2025-10-29T...",
    "listing_id": 1
  }
]
```

#### 2g. Mark Notification as Read
```bash
curl -X PATCH "http://localhost:8000/buyer/notifications/1/mark-read" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### **STEP 3: Test Notification Preferences Endpoints**

#### 3a. Get Notification Preferences
```bash
curl -X GET "http://localhost:8000/notification-preferences" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response**:
```json
{
  "user_id": 1,
  "email_notifications": true,
  "notification_channels": ["email"],
  "notification_frequency": "instant",
  "deal_alerts_enabled": true,
  "deal_alert_min_score": 7.0,
  "order_notifications_enabled": true,
  "marketplace_notifications_enabled": true,
  "promotional_emails": false
}
```

#### 3b. Update Notification Preferences
```bash
curl -X PUT "http://localhost:8000/notification-preferences?email_notifications=true&notification_frequency=daily_digest&deal_alert_min_score=8.0&promotional_emails=false" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response**:
```json
{
  "message": "Notification preferences updated successfully",
  "preferences": { ... }
}
```

#### 3c. Get Available Channels
```bash
curl -X GET "http://localhost:8000/notification-preferences/channels-available"
```

**Expected Response**:
```json
{
  "channels": [
    {
      "id": "email",
      "name": "Email",
      "description": "Receive notifications via email"
    },
    {
      "id": "discord",
      "name": "Discord",
      "description": "Receive notifications via Discord webhook"
    },
    {
      "id": "sms",
      "name": "SMS",
      "description": "Receive notifications via SMS (Twilio)"
    },
    {
      "id": "push",
      "name": "Push Notification",
      "description": "Receive web/mobile push notifications"
    }
  ]
}
```

#### 3d. Get Available Frequencies
```bash
curl -X GET "http://localhost:8000/notification-preferences/frequencies-available"
```

#### 3e. View Notification History
```bash
curl -X GET "http://localhost:8000/notification-preferences/history?limit=50&status_filter=read" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 3f. Mark All Notifications as Read
```bash
curl -X POST "http://localhost:8000/notification-preferences/mark-all-read" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 3g. Clear All Notifications
```bash
curl -X POST "http://localhost:8000/notification-preferences/clear" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### **STEP 4: Test Marketplace Account Endpoints**

Use the seller's access token.

#### 4a. List Marketplace Accounts
```bash
curl -X GET "http://localhost:8000/marketplace-accounts" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

**Expected Response** (empty initially):
```json
[]
```

#### 4b. Create eBay Marketplace Account
```bash
curl -X POST "http://localhost:8000/marketplace-accounts?platform=ebay&account_username=myebaystore" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

**Expected Response**:
```json
{
  "id": 1,
  "platform": "ebay",
  "account_username": "myebaystore",
  "is_active": true,
  "message": "Marketplace account for ebay created successfully"
}
```

#### 4c. List Again (Should See Account)
```bash
curl -X GET "http://localhost:8000/marketplace-accounts" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

#### 4d. Create Facebook Marketplace Account
```bash
curl -X POST "http://localhost:8000/marketplace-accounts?platform=facebook&account_username=myfacebookpage" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

#### 4e. Get Specific Account
```bash
curl -X GET "http://localhost:8000/marketplace-accounts/1" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

#### 4f. Update Account
```bash
curl -X PATCH "http://localhost:8000/marketplace-accounts/1?account_username=newusername&is_active=true" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

#### 4g. Disconnect Account (Disable without Deleting)
```bash
curl -X POST "http://localhost:8000/marketplace-accounts/1/disconnect" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

#### 4h. Reconnect Account
```bash
curl -X POST "http://localhost:8000/marketplace-accounts/1/reconnect" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

#### 4i. Delete Account
```bash
curl -X DELETE "http://localhost:8000/marketplace-accounts/1" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

---

### **STEP 5: Test Snap Studio (Seller) Endpoints**

#### 5a. Create a Snap Job
```bash
curl -X POST "http://localhost:8000/seller/snap" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN" \
  -d '{
    "photos": ["https://example.com/photo1.jpg"],
    "notes": "Nice couch, good condition",
    "source": "upload"
  }'
```

**Expected Response**:
```json
{
  "job_id": 1,
  "status": "queued"
}
```

#### 5b. Get Snap Job Status
```bash
curl -X GET "http://localhost:8000/seller/snap/1" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

**Expected Response**:
```json
{
  "job_id": 1,
  "status": "queued",
  "title": null,
  "description": null,
  "suggested_price": null,
  "condition_guess": null,
  "processed_images": [],
  "images": ["https://example.com/photo1.jpg"],
  "created_at": "2025-10-29T..."
}
```

**Note**: The job will stay in "queued" unless the Celery worker is running. It will process in the background.

#### 5c. List Snap Jobs
```bash
curl -X GET "http://localhost:8000/seller/snap?limit=20" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

#### 5d. Publish Snap to Marketplace (Cross-Posting)
```bash
curl -X POST "http://localhost:8000/seller/snap/1/publish" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN" \
  -d '{
    "snap_job_id": 1,
    "platforms": ["ebay", "facebook"],
    "price": 200.0,
    "notes": "Cross-posting to multiple platforms"
  }'
```

**Expected Response**:
```json
{
  "cross_post_id": 1,
  "item_id": 1,
  "platforms": ["ebay", "facebook"],
  "status": "pending",
  "created_at": "2025-10-29T..."
}
```

---

### **STEP 6: Test Pricing Endpoints**

#### 6a. Get Available Categories
```bash
curl -X GET "http://localhost:8000/seller/pricing/categories"
```

**Expected Response**:
```json
{
  "categories": ["furniture>sofas", "kitchen>islands"]
}
```

#### 6b. Get Pricing Stats
```bash
curl -X GET "http://localhost:8000/seller/pricing/stats?category=furniture%3Esofas&condition=good"
```

**Expected Response**:
```json
{
  "category": "furniture>sofas",
  "condition": "good",
  "count": 5,
  "min_price": 100.0,
  "max_price": 500.0,
  "avg_price": 300.0,
  "median_price": 300.0,
  "stddev": 150.5
}
```

#### 6c. Get Market Trends
```bash
curl -X GET "http://localhost:8000/seller/pricing/market-trends?category=furniture%3Esofas&days=30"
```

**Expected Response**:
```json
{
  "category": "furniture>sofas",
  "period_days": 30,
  "total_comps": 5,
  "overall": {
    "min": 100.0,
    "max": 500.0,
    "avg": 300.0,
    "median": 300.0,
    "stddev": 150.5
  },
  "by_condition": {
    "good": {
      "count": 3,
      "min": 150.0,
      "max": 400.0,
      "avg": 275.0,
      "median": 300.0
    },
    "excellent": {
      "count": 2,
      "min": 350.0,
      "max": 500.0,
      "avg": 425.0,
      "median": 425.0
    }
  }
}
```

#### 6d. List Your Items
```bash
curl -X GET "http://localhost:8000/seller/pricing/my-items" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN"
```

#### 6e. Create a Comparable Listing
```bash
curl -X POST "http://localhost:8000/seller/pricing/comps" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SELLER_TOKEN" \
  -d '{
    "category": "furniture>sofas",
    "title": "Blue Sectional Couch",
    "price": 350.0,
    "condition": "good",
    "source": "ebay",
    "metadata": {"size": "L-shaped", "color": "blue"}
  }'
```

---

## Testing Without Initial Data

If you're not seeing any deals or comps, you need test data. Here are options:

### Option A: Use FastAPI Docs (Recommended for Manual Testing)
```
Visit: http://localhost:8000/docs
```
This gives you an interactive Swagger UI where you can:
1. Authorize with a token
2. Execute endpoints with real-time responses
3. See request/response examples

### Option B: Seed Test Data via Script
If there's a seed script available:
```bash
docker compose exec backend python scripts/seed_mock_data.py
```

### Option C: Manually Insert Listings via Database
```bash
docker compose exec postgres psql -U deals -d deals -c "
INSERT INTO listings (title, price, category, condition)
VALUES ('Test Couch', 150, 'furniture>sofas', 'good');
"
```

---

## Error Testing

### Test Missing Authentication
```bash
curl -X GET "http://localhost:8000/buyer/deals"
```
**Expected**: 401 Unauthorized

### Test Invalid Token
```bash
curl -X GET "http://localhost:8000/buyer/deals" \
  -H "Authorization: Bearer invalid_token"
```
**Expected**: 401 Unauthorized

### Test Role-Based Access (Buyer accessing Seller endpoint)
```bash
curl -X POST "http://localhost:8000/seller/snap" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer BUYER_TOKEN" \
  -d '{"photos": ["test.jpg"]}'
```
**Expected**: 403 Forbidden (Seller access required)

### Test Non-Existent Resource
```bash
curl -X GET "http://localhost:8000/buyer/notifications/99999" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: 404 Not Found

### Test Invalid Frequency
```bash
curl -X PUT "http://localhost:8000/notification-preferences?notification_frequency=invalid_frequency" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: 400 Bad Request

---

## Using Postman for Testing

1. **Import the endpoints as a collection**:
   - Create a new Postman Collection
   - Add folders: Authentication, Buyer, Seller, Marketplace, Notifications, Pricing

2. **Set environment variables**:
   - `base_url`: `http://localhost:8000`
   - `access_token`: (populate after auth)
   - `seller_token`: (populate after seller registration)

3. **Use Pre-request scripts** to handle token refresh:
   ```javascript
   // This script runs before each request
   // Can automatically refresh expired tokens
   ```

4. **Use Tests tab** for validation:
   ```javascript
   pm.test("Status code is 200", function () {
       pm.response.to.have.status(200);
   });
   ```

---

## Automated Testing with Python

Create `test_phase4.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_authentication():
    """Test user registration and login"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return token

def test_buyer_deals(token):
    """Test buyer endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/buyer/deals",
        headers=headers
    )
    assert response.status_code == 200
    print("Buyer deals:", response.json())

def test_notification_preferences(token):
    """Test notification preferences"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/notification-preferences",
        headers=headers
    )
    assert response.status_code == 200
    print("Notification preferences:", response.json())

if __name__ == "__main__":
    token = test_authentication()
    test_buyer_deals(token)
    test_notification_preferences(token)
    print("✅ All tests passed!")
```

Run it:
```bash
python test_phase4.py
```

---

## Checklist for Complete Testing

- [ ] Can register buyer user
- [ ] Can register seller user
- [ ] Can list deals (GET /buyer/deals)
- [ ] Can save deal (POST /buyer/deals/{id}/save)
- [ ] Can get saved deals
- [ ] Can update buyer preferences
- [ ] Can get/update notification preferences
- [ ] Can list marketplace accounts
- [ ] Can create marketplace account (eBay)
- [ ] Can create snap job
- [ ] Can publish snap with cross-posting
- [ ] Can get pricing stats
- [ ] Can get market trends
- [ ] Can create comparable listing
- [ ] All error cases return correct status codes
- [ ] Seller cannot access buyer endpoints with wrong token
- [ ] Tokens expire appropriately
- [ ] Pagination works on list endpoints

---

## Performance Testing

Check response times for key endpoints:

```bash
# Measure time to list deals (should be <500ms)
time curl "http://localhost:8000/buyer/deals?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Measure time to get pricing stats (should be <1s)
time curl "http://localhost:8000/seller/pricing/stats?category=furniture%3Esofas"
```

---

## Conclusion

You now have a complete testing roadmap for Phase 4! Start with Step 1 (Authentication), then work through each section systematically. The FastAPI docs at `/docs` is your best interactive testing tool.

Good luck! 🚀
