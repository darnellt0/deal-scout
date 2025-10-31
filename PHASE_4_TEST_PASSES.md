# Phase 4 - Test Passes & Edge Case Testing

Complete testing workflows for Phase 4 endpoints. Use these step-by-step test passes to verify functionality.

---

## Setup

Before running test passes, ensure:
- Backend is running: `docker compose up -d`
- Get a JWT token using one of these methods:
  - Call `/auth/register` endpoint and save the `access_token`
  - Use the `mint_jwt_tokens.py` script: `python mint_jwt_tokens.py --buyer`
- Save token to environment or VS Code REST Client `@token` variable

---

## Test Pass A: Buyer Flow (5 minutes)

**Goal**: Verify complete buyer journey from registration through saved deals

### A1. Register as Buyer
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "buyer_test_'"$(date +%s)"'",
    "email": "buyer_'"$(date +%s)"'@example.com",
    "password": "BuyerPassword123"
  }'
```

**Expected**: HTTP 201, returns `access_token` and user info
**Save**: Copy `access_token` value

### A2. Get Available Deals
```bash
curl -X GET "http://localhost:8000/buyer/deals?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns array of deals with:
- `id`, `title`, `price`, `condition`, `score`
- `description`, `source_url`, `user_id`

**Success Criteria**: At least 1 deal returned

### A3. Filter Deals by Category
```bash
curl -X GET "http://localhost:8000/buyer/deals?category=furniture&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns only furniture deals

### A4. Filter Deals by Price Range
```bash
curl -X GET "http://localhost:8000/buyer/deals?max_price=500" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, all returned deals have price ≤ 500

### A5. Filter Deals by Score
```bash
curl -X GET "http://localhost:8000/buyer/deals?min_score=8.0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, all deals have score ≥ 8.0

### A6. Save a Deal
```bash
curl -X POST "http://localhost:8000/buyer/deals/1/save" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns saved deal info

**Note**: Use a valid deal ID from step A2

### A7. Get Saved Deals
```bash
curl -X GET "http://localhost:8000/buyer/deals/saved" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns array including the deal saved in A6

### A8. Unsave a Deal
```bash
curl -X DELETE "http://localhost:8000/buyer/deals/1/save" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, deal no longer appears in saved deals

### A9. Get Buyer Preferences
```bash
curl -X GET "http://localhost:8000/buyer/preferences" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns preferences with:
- `search_radius_mi`, `max_price_couch`, `max_price_desk`, etc.
- `preferred_condition`, `notification_enabled`

### A10. Update Buyer Preferences
```bash
curl -X PUT "http://localhost:8000/buyer/preferences?search_radius_mi=30&max_price_couch=3000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, preferences updated

### A11. Verify Preferences Were Updated
```bash
curl -X GET "http://localhost:8000/buyer/preferences" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, `search_radius_mi` is now 30

---

## Test Pass B: Seller Snap & Cross-Posting (5 minutes)

**Goal**: Verify snap studio job creation and marketplace publishing

### B1. Register as Seller
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seller_test_'"$(date +%s)"'",
    "email": "seller_'"$(date +%s)"'@example.com",
    "password": "SellerPassword123"
  }'
```

**Expected**: HTTP 201, returns seller access_token
**Save**: Copy token

### B2. Create First Marketplace Account (eBay)
```bash
curl -X POST "http://localhost:8000/marketplace-accounts?platform=ebay&account_username=my_ebay_store" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 201, returns account with:
- `id`, `platform` (ebay), `account_username`, `is_connected`
- `created_at`, `user_id`

**Save**: Copy `id` for later use

### B3. Create Second Marketplace Account (Facebook)
```bash
curl -X POST "http://localhost:8000/marketplace-accounts?platform=facebook&account_username=my_fb_page" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 201, returns Facebook account

### B4. Create Snap Job
```bash
curl -X POST "http://localhost:8000/seller/snap" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "photos": [
      "https://example.com/couch1.jpg",
      "https://example.com/couch2.jpg"
    ],
    "notes": "Beautiful couch, barely used, non-smoking home",
    "source": "upload"
  }'
```

**Expected**: HTTP 201, returns snap job with:
- `job_id`, `status` (should be "pending"), `user_id`
- `photo_count`, `created_at`

**Save**: Copy `job_id`

### B5. Get Snap Job Status
```bash
curl -X GET "http://localhost:8000/seller/snap/JOB_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, shows job details with current status

**Replace**: `JOB_ID` with the ID from B4

### B6. List All Snap Jobs
```bash
curl -X GET "http://localhost:8000/seller/snap?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns array including the snap job from B4

### B7. Publish Snap to Marketplaces
```bash
curl -X POST "http://localhost:8000/seller/snap/JOB_ID/publish" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Beautiful Couch - Excellent Condition",
    "description": "Gently used, excellent condition, smoke-free home",
    "platforms": ["ebay", "facebook"]
  }'
```

**Expected**: HTTP 201, returns cross-post record with:
- `id`, `snap_job_id`, `platforms`, `status` (should be "pending")
- `created_at`

**Note**: Task enqueued for background processing

---

## Test Pass C: Marketplace Account Management (3 minutes)

**Goal**: Verify full CRUD operations on marketplace accounts

### C1. List All Marketplace Accounts
```bash
curl -X GET "http://localhost:8000/marketplace-accounts" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns array of accounts

### C2. Get Specific Account (Use ID from B2)
```bash
curl -X GET "http://localhost:8000/marketplace-accounts/ACCOUNT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns single account detail

### C3. Update Account
```bash
curl -X PATCH "http://localhost:8000/marketplace-accounts/ACCOUNT_ID?platform=ebay&account_username=updated_store_name" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, account username updated

### C4. Disconnect Account
```bash
curl -X POST "http://localhost:8000/marketplace-accounts/ACCOUNT_ID/disconnect" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, `is_connected` becomes false

### C5. Reconnect Account
```bash
curl -X POST "http://localhost:8000/marketplace-accounts/ACCOUNT_ID/reconnect" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, `is_connected` becomes true

### C6. Delete Account
```bash
curl -X DELETE "http://localhost:8000/marketplace-accounts/ACCOUNT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, message confirms deletion

### C7. Verify Deletion (Try to get deleted account)
```bash
curl -X GET "http://localhost:8000/marketplace-accounts/ACCOUNT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 404, account not found

---

## Test Pass D: Notification Preferences (3 minutes)

**Goal**: Verify notification configuration endpoints

### D1. Get Current Notification Preferences
```bash
curl -X GET "http://localhost:8000/notification-preferences" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns preferences with:
- `notification_frequency` (instant/daily_digest/weekly_digest)
- `email_notifications`, `push_notifications`, `deal_alert_min_score`
- `user_id`, `created_at`, `updated_at`

### D2. Update Notification Frequency
```bash
curl -X PUT "http://localhost:8000/notification-preferences?notification_frequency=daily_digest" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, frequency updated

### D3. Update Deal Alert Score Threshold
```bash
curl -X PUT "http://localhost:8000/notification-preferences?deal_alert_min_score=8.5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, score threshold updated

### D4. Enable Email Notifications
```bash
curl -X PUT "http://localhost:8000/notification-preferences?email_notifications=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, email notifications enabled

### D5. Get Available Channels
```bash
curl -X GET "http://localhost:8000/notification-preferences/channels-available" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns list of channel options (email, discord, sms, push, etc.)

### D6. Get Available Frequencies
```bash
curl -X GET "http://localhost:8000/notification-preferences/frequencies-available" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns list: ["instant", "daily_digest", "weekly_digest"]

### D7. Reset to Defaults
```bash
curl -X POST "http://localhost:8000/notification-preferences/reset" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, all settings reset to defaults

### D8. Get Notification History
```bash
curl -X GET "http://localhost:8000/notification-preferences/history" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns history array (may be empty initially)

### D9. Mark All as Read
```bash
curl -X POST "http://localhost:8000/notification-preferences/mark-all-read" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, all notifications marked as read

### D10. Clear All Notifications
```bash
curl -X POST "http://localhost:8000/notification-preferences/clear" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, notifications cleared

---

## Test Pass E: Pricing & Market Analysis (3 minutes)

**Goal**: Verify pricing endpoints for seller analysis

### E1. Get Available Product Categories
```bash
curl -X GET "http://localhost:8000/seller/pricing/categories"
```

**Expected**: HTTP 200 (no auth required), returns object with `categories` array:
```json
{
  "categories": [
    "furniture>sofas",
    "furniture>desks",
    "electronics>phones",
    ...
  ]
}
```

**Save**: Pick one category for next steps (e.g., "furniture>sofas")

### E2. Get Price Statistics for Category
```bash
curl -X GET "http://localhost:8000/seller/pricing/stats?category=furniture%3Esofas" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns breakdown:
```json
{
  "category": "furniture>sofas",
  "total_listings": 42,
  "conditions": {
    "new": { "count": 5, "min": 2000, "max": 3500, "avg": 2750, "median": 2800 },
    "good": { "count": 25, "min": 800, "max": 2000, "avg": 1400, "median": 1350 },
    ...
  }
}
```

### E3. Get Market Trends (30 days)
```bash
curl -X GET "http://localhost:8000/seller/pricing/market-trends?category=furniture%3Esofas&days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns trend analysis:
```json
{
  "category": "furniture>sofas",
  "period_days": 30,
  "trend_direction": "stable" | "increasing" | "decreasing",
  "avg_price_start": 1350,
  "avg_price_end": 1400,
  "price_change_percent": 3.7,
  "conditions": {
    "new": { trend_direction, avg_price_change },
    "good": { trend_direction, avg_price_change },
    ...
  }
}
```

### E4. Get Your Listed Items
```bash
curl -X GET "http://localhost:8000/seller/pricing/my-items" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: HTTP 200, returns array of your items:
```json
[
  {
    "id": 1,
    "title": "Leather Sofa",
    "category": "furniture>sofas",
    "condition": "good",
    "your_price": 1200,
    "market_avg": 1400,
    "market_min": 800,
    "market_max": 2000
  }
]
```

### E5. Create Comparable Listing Record
```bash
curl -X POST "http://localhost:8000/seller/pricing/comps" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "furniture>sofas",
    "title": "Mid-Century Modern Sofa - Good Condition",
    "condition": "good",
    "price": 1350,
    "url": "https://marketplace.example.com/listing/12345"
  }'
```

**Expected**: HTTP 201, returns:
```json
{
  "id": 1,
  "category": "furniture>sofas",
  "title": "Mid-Century Modern Sofa - Good Condition",
  "condition": "good",
  "price": 1350,
  "user_id": 2,
  "created_at": "2025-10-28T12:34:56"
}
```

---

## Edge Case Testing

### EC1: Authentication Edge Cases

**EC1a. Missing Authorization Header**
```bash
curl -X GET "http://localhost:8000/buyer/deals"
```
**Expected**: HTTP 401, message "Not authenticated"

**EC1b. Invalid Token**
```bash
curl -X GET "http://localhost:8000/buyer/deals" \
  -H "Authorization: Bearer invalid_token_xyz"
```
**Expected**: HTTP 401, message "Invalid authentication credentials"

**EC1c. Expired Token**
- Generate a token, wait for expiration, try to use it
**Expected**: HTTP 401, "Token has expired"

**EC1d. Malformed Authorization Header**
```bash
curl -X GET "http://localhost:8000/buyer/deals" \
  -H "Authorization: InvalidScheme token_here"
```
**Expected**: HTTP 401

---

### EC2: Authorization/RBAC Edge Cases

**EC2a. Buyer Trying to Access Seller Endpoint**
```bash
# Register as buyer, then:
curl -X POST "http://localhost:8000/seller/snap" \
  -H "Authorization: Bearer BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"photos": ["url"], "notes": "test", "source": "upload"}'
```
**Expected**: HTTP 403, "Seller access required"

**EC2b. Non-Admin Trying to Access Admin Endpoint**
- If there are admin-only endpoints
**Expected**: HTTP 403

**EC2c. Accessing Own Resources vs. Others**
```bash
# User 1 tries to access User 2's preferences
curl -X GET "http://localhost:8000/buyer/preferences" \
  -H "Authorization: Bearer USER2_TOKEN"
```
**Expected**: HTTP 200 (returns own preferences, not user 1's)

---

### EC3: Validation & 422 Errors

**EC3a. Invalid Notification Frequency**
```bash
curl -X PUT "http://localhost:8000/notification-preferences?notification_frequency=invalid_value" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 422, validation error listing valid values

**EC3b. Invalid Deal Alert Score (Out of Range)**
```bash
curl -X PUT "http://localhost:8000/notification-preferences?deal_alert_min_score=15" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 422, "score must be between 0 and 10"

**EC3c. Negative Price in Preferences**
```bash
curl -X PUT "http://localhost:8000/buyer/preferences?max_price_couch=-100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 422, "price must be positive"

**EC3d. Negative Search Radius**
```bash
curl -X PUT "http://localhost:8000/buyer/preferences?search_radius_mi=-5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 422, "radius must be positive"

---

### EC4: 404 Not Found Cases

**EC4a. Non-Existent Deal**
```bash
curl -X POST "http://localhost:8000/buyer/deals/999999/save" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 404, "Deal not found"

**EC4b. Non-Existent Notification**
```bash
curl -X GET "http://localhost:8000/buyer/notifications/999999" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 404, "Notification not found"

**EC4c. Non-Existent Marketplace Account**
```bash
curl -X DELETE "http://localhost:8000/marketplace-accounts/999999" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 404, "Account not found"

**EC4d. Non-Existent Snap Job**
```bash
curl -X GET "http://localhost:8000/seller/snap/999999" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 404, "Job not found"

---

### EC5: 409 Conflict Cases

**EC5a. Duplicate Marketplace Account (Same Platform)**
```bash
# Create eBay account
curl -X POST "http://localhost:8000/marketplace-accounts?platform=ebay&account_username=store1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Try to create another eBay account for same user
curl -X POST "http://localhost:8000/marketplace-accounts?platform=ebay&account_username=store2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 409, "You already have an account for this platform"

**EC5b. Duplicate Registration (Same Email)**
```bash
# First registration succeeds
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "email": "same@example.com", "password": "Pass123"}'

# Try to register with same email
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user2", "email": "same@example.com", "password": "Pass123"}'
```
**Expected**: HTTP 409, "Email already registered"

**EC5c. Duplicate Registration (Same Username)**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "duplicate_user", "email": "a@example.com", "password": "Pass123"}'

curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "duplicate_user", "email": "b@example.com", "password": "Pass123"}'
```
**Expected**: HTTP 409, "Username already taken"

---

### EC6: Invalid Request Body Cases

**EC6a. Missing Required Fields**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1"}'  # Missing email and password
```
**Expected**: HTTP 422, lists missing fields

**EC6b. Invalid Email Format**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "email": "not-an-email", "password": "Pass123"}'
```
**Expected**: HTTP 422, "Invalid email format"

**EC6c. Password Too Short**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "email": "test@example.com", "password": "short"}'
```
**Expected**: HTTP 422, "Password must be at least 8 characters"

**EC6d. Invalid JSON in Request Body**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{invalid json}'
```
**Expected**: HTTP 422, JSON parsing error

---

### EC7: Boundary Cases

**EC7a. Pagination Limits**
```bash
# Request more items than max allowed
curl -X GET "http://localhost:8000/buyer/deals?limit=10000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 200 (limit capped at max, e.g., 50)

**EC7b. Filter with No Results**
```bash
curl -X GET "http://localhost:8000/buyer/deals?category=nonexistent_category" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: HTTP 200, empty array

**EC7c. Query String Case Sensitivity**
```bash
curl -X GET "http://localhost:8000/buyer/deals?Category=furniture" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected**: Should handle gracefully (case-insensitive or error)

---

## Load Testing (Optional)

### Lightweight Load Test with curl

Test 10 concurrent requests to deals endpoint:

```bash
#!/bin/bash
# save as test_load.sh

TOKEN="your_token_here"
BASE_URL="http://localhost:8000"

for i in {1..10}; do
  curl -s -X GET "${BASE_URL}/buyer/deals?limit=5" \
    -H "Authorization: Bearer ${TOKEN}" > /dev/null &
done
wait
echo "✅ 10 concurrent requests completed"
```

Run:
```bash
chmod +x test_load.sh
./test_load.sh
```

### Moderate Load Test with PowerShell

```powershell
# test_load.ps1

$token = "your_token_here"
$baseUrl = "http://localhost:8000"
$numRequests = 25

$sw = [System.Diagnostics.Stopwatch]::StartNew()

for ($i = 0; $i -lt $numRequests; $i++) {
  $headers = @{
    "Authorization" = "Bearer $token"
  }

  Invoke-RestMethod -Uri "$baseUrl/buyer/deals?limit=5" `
    -Headers $headers `
    -Method Get | Out-Null
}

$sw.Stop()
Write-Host "✅ Completed $numRequests requests in $($sw.ElapsedMilliseconds)ms"
Write-Host "Avg per request: $($sw.ElapsedMilliseconds / $numRequests)ms"
```

---

## Summary Checklist

Use this checklist to verify all test passes:

### Test Pass A (Buyer Flow)
- [ ] A1: Register user
- [ ] A2: Get deals
- [ ] A3: Filter by category
- [ ] A4: Filter by price
- [ ] A5: Filter by score
- [ ] A6: Save deal
- [ ] A7: View saved deals
- [ ] A8: Unsave deal
- [ ] A9: Get preferences
- [ ] A10: Update preferences
- [ ] A11: Verify update

### Test Pass B (Seller Snap)
- [ ] B1: Register seller
- [ ] B2: Create eBay account
- [ ] B3: Create Facebook account
- [ ] B4: Create snap job
- [ ] B5: Get snap status
- [ ] B6: List snap jobs
- [ ] B7: Publish to marketplaces

### Test Pass C (Marketplace Management)
- [ ] C1: List accounts
- [ ] C2: Get account details
- [ ] C3: Update account
- [ ] C4: Disconnect account
- [ ] C5: Reconnect account
- [ ] C6: Delete account
- [ ] C7: Verify deletion

### Test Pass D (Notifications)
- [ ] D1: Get preferences
- [ ] D2: Update frequency
- [ ] D3: Update score threshold
- [ ] D4: Enable email
- [ ] D5: List channels
- [ ] D6: List frequencies
- [ ] D7: Reset to defaults
- [ ] D8: Get history
- [ ] D9: Mark all read
- [ ] D10: Clear all

### Test Pass E (Pricing)
- [ ] E1: Get categories
- [ ] E2: Get stats
- [ ] E3: Get trends
- [ ] E4: Get your items
- [ ] E5: Create comparable

### Edge Cases
- [ ] EC1: Auth edge cases
- [ ] EC2: RBAC edge cases
- [ ] EC3: Validation (422)
- [ ] EC4: Not found (404)
- [ ] EC5: Conflicts (409)
- [ ] EC6: Bad requests
- [ ] EC7: Boundaries

---

**All tests passing? 🎉 Phase 4 is solid and ready for Phase 5!**
