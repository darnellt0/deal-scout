# Phase 4 Testing Cheat Sheet

Quick reference for common testing scenarios. Copy and paste commands directly.

---

## Setup (Do This First)

```bash
# Start backend
cd /path/to/deal-scout
docker compose up -d

# Generate test token
python mint_jwt_tokens.py --buyer
# Copy the token from output

# Or register manually
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"testuser",
    "email":"testuser@example.com",
    "password":"TestPass123"
  }'
# Copy access_token from response
```

---

## Essential Commands

**Set token in terminal** (for copy-paste commands):
```bash
TOKEN="your_token_here"
BASE="http://localhost:8000"
```

---

## Buyer Endpoints

### Register User
```bash
curl -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"buyer_'$(date +%s)'",
    "email":"buyer_'$(date +%s)'@example.com",
    "password":"Password123"
  }'
```

### Get Deals
```bash
curl -X GET "$BASE/buyer/deals?limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Deals with Filters
```bash
# By category
curl -X GET "$BASE/buyer/deals?category=furniture" \
  -H "Authorization: Bearer $TOKEN"

# By price
curl -X GET "$BASE/buyer/deals?max_price=1000" \
  -H "Authorization: Bearer $TOKEN"

# By score
curl -X GET "$BASE/buyer/deals?min_score=8.0" \
  -H "Authorization: Bearer $TOKEN"

# Combined
curl -X GET "$BASE/buyer/deals?category=furniture&max_price=1500&min_score=7.0" \
  -H "Authorization: Bearer $TOKEN"
```

### Save Deal (replace {id} with deal ID)
```bash
curl -X POST "$BASE/buyer/deals/1/save" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Saved Deals
```bash
curl -X GET "$BASE/buyer/deals/saved" \
  -H "Authorization: Bearer $TOKEN"
```

### Unsave Deal
```bash
curl -X DELETE "$BASE/buyer/deals/1/save" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Your Preferences
```bash
curl -X GET "$BASE/buyer/preferences" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Preferences
```bash
curl -X PUT "$BASE/buyer/preferences?search_radius_mi=25&max_price_couch=2500" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Notification Preferences

### Get Notification Settings
```bash
curl -X GET "$BASE/notification-preferences" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Notification Frequency
```bash
# instant, daily_digest, or weekly_digest
curl -X PUT "$BASE/notification-preferences?notification_frequency=daily_digest" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Alert Threshold
```bash
curl -X PUT "$BASE/notification-preferences?deal_alert_min_score=8.0" \
  -H "Authorization: Bearer $TOKEN"
```

### Enable/Disable Email
```bash
curl -X PUT "$BASE/notification-preferences?email_notifications=true" \
  -H "Authorization: Bearer $TOKEN"
```

### List Available Channels
```bash
curl -X GET "$BASE/notification-preferences/channels-available" \
  -H "Authorization: Bearer $TOKEN"
```

### List Available Frequencies
```bash
curl -X GET "$BASE/notification-preferences/frequencies-available" \
  -H "Authorization: Bearer $TOKEN"
```

### Mark All Read
```bash
curl -X POST "$BASE/notification-preferences/mark-all-read" \
  -H "Authorization: Bearer $TOKEN"
```

### Reset to Defaults
```bash
curl -X POST "$BASE/notification-preferences/reset" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Marketplace Accounts

### Create Account
```bash
# eBay
curl -X POST "$BASE/marketplace-accounts?platform=ebay&account_username=mystore" \
  -H "Authorization: Bearer $TOKEN"

# Facebook
curl -X POST "$BASE/marketplace-accounts?platform=facebook&account_username=my_page" \
  -H "Authorization: Bearer $TOKEN"
```

### List Your Accounts
```bash
curl -X GET "$BASE/marketplace-accounts" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Single Account
```bash
curl -X GET "$BASE/marketplace-accounts/1" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Account
```bash
curl -X PATCH "$BASE/marketplace-accounts/1?account_username=new_username" \
  -H "Authorization: Bearer $TOKEN"
```

### Disconnect Account
```bash
curl -X POST "$BASE/marketplace-accounts/1/disconnect" \
  -H "Authorization: Bearer $TOKEN"
```

### Reconnect Account
```bash
curl -X POST "$BASE/marketplace-accounts/1/reconnect" \
  -H "Authorization: Bearer $TOKEN"
```

### Delete Account
```bash
curl -X DELETE "$BASE/marketplace-accounts/1" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Snap Studio (Seller)

### Create Snap Job
```bash
curl -X POST "$BASE/seller/snap" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "photos": [
      "https://example.com/photo1.jpg",
      "https://example.com/photo2.jpg"
    ],
    "notes": "Beautiful couch, excellent condition",
    "source": "upload"
  }'
```

### Get Snap Status
```bash
curl -X GET "$BASE/seller/snap/1" \
  -H "Authorization: Bearer $TOKEN"
```

### List All Snaps
```bash
curl -X GET "$BASE/seller/snap?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Publish to Marketplace
```bash
curl -X POST "$BASE/seller/snap/1/publish" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Beautiful Couch - Excellent Condition",
    "description": "Gently used couch, smoke-free home",
    "platforms": ["ebay", "facebook"]
  }'
```

---

## Pricing Endpoints

### Get Product Categories
```bash
curl -X GET "$BASE/seller/pricing/categories"
```

### Get Price Statistics
```bash
curl -X GET "$BASE/seller/pricing/stats?category=furniture%3Esofas" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Market Trends
```bash
curl -X GET "$BASE/seller/pricing/market-trends?category=furniture%3Esofas&days=30" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Your Items
```bash
curl -X GET "$BASE/seller/pricing/my-items" \
  -H "Authorization: Bearer $TOKEN"
```

### Add Comparable
```bash
curl -X POST "$BASE/seller/pricing/comps" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "furniture>sofas",
    "title": "Mid-Century Sofa",
    "condition": "good",
    "price": 1350.00,
    "url": "https://example.com/listing"
  }'
```

---

## Error Testing

### 401: Missing Token
```bash
curl -X GET "$BASE/buyer/deals"
```

### 401: Invalid Token
```bash
curl -X GET "$BASE/buyer/deals" \
  -H "Authorization: Bearer invalid_token"
```

### 403: Non-Seller Trying Seller Endpoint
```bash
# Register as buyer first, then:
curl -X POST "$BASE/seller/snap" \
  -H "Authorization: Bearer $BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"photos":["url"],"notes":"test","source":"upload"}'
```

### 404: Non-Existent Resource
```bash
curl -X GET "$BASE/buyer/deals/999999/save" \
  -H "Authorization: Bearer $TOKEN"
```

### 409: Duplicate Platform
```bash
# Create first account
curl -X POST "$BASE/marketplace-accounts?platform=ebay&account_username=store1" \
  -H "Authorization: Bearer $TOKEN"

# Try to create another for same platform
curl -X POST "$BASE/marketplace-accounts?platform=ebay&account_username=store2" \
  -H "Authorization: Bearer $TOKEN"
```

### 422: Invalid Frequency
```bash
curl -X PUT "$BASE/notification-preferences?notification_frequency=invalid" \
  -H "Authorization: Bearer $TOKEN"
```

### 422: Missing Required Field
```bash
curl -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"test"}'  # Missing email and password
```

---

## Common Test Patterns

### Test Complete Buyer Flow (One Command)
```bash
#!/bin/bash

TOKEN="$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test_'$(date +%s)'","email":"test_'$(date +%s)'@example.com","password":"Pass123"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)"

echo "Token: $TOKEN"

# Get deals
echo "Getting deals..."
curl -s -X GET "http://localhost:8000/buyer/deals?limit=3" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Save deal
echo "Saving deal 1..."
curl -s -X POST "http://localhost:8000/buyer/deals/1/save" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Get saved deals
echo "Getting saved deals..."
curl -s -X GET "http://localhost:8000/buyer/deals/saved" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### Test All Endpoints Rapidly (Bash Loop)
```bash
#!/bin/bash

BASE="http://localhost:8000"
TOKEN="your_token_here"

endpoints=(
  "GET /buyer/deals"
  "GET /buyer/deals/saved"
  "GET /buyer/preferences"
  "GET /buyer/notifications"
  "GET /notification-preferences"
  "GET /marketplace-accounts"
  "GET /seller/snap"
  "GET /seller/pricing/categories"
)

for endpoint in "${endpoints[@]}"; do
  method=$(echo $endpoint | cut -d' ' -f1)
  path=$(echo $endpoint | cut -d' ' -f2)

  echo "Testing: $endpoint"
  curl -s -X $method "$BASE$path" \
    -H "Authorization: Bearer $TOKEN" \
    -w "\nStatus: %{http_code}\n\n"
done
```

### PowerShell: Test Rapidly
```powershell
$token = "your_token_here"
$base = "http://localhost:8000"

$endpoints = @(
  "GET /buyer/deals",
  "GET /buyer/deals/saved",
  "GET /buyer/preferences",
  "GET /marketplace-accounts",
  "GET /seller/pricing/categories"
)

foreach ($endpoint in $endpoints) {
  $parts = $endpoint -split ' '
  $method = $parts[0]
  $path = $parts[1]

  Write-Host "Testing: $endpoint"

  $headers = @{
    "Authorization" = "Bearer $token"
  }

  try {
    $response = Invoke-RestMethod -Uri "$base$path" `
      -Headers $headers `
      -Method $method
    Write-Host "✅ Success" -ForegroundColor Green
  } catch {
    Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
  }

  Write-Host ""
}
```

---

## Quick Status Check

```bash
#!/bin/bash

BASE="http://localhost:8000"
TOKEN="your_token_here"

echo "Phase 4 Status Check"
echo "===================="

# Check backend
echo -n "Backend: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs && echo " ✅" || echo " ❌"

# Check auth
echo -n "Auth: "
curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"status_check_'$(date +%s)'","email":"check@example.com","password":"Pass123"}' \
  -o /dev/null -w "%{http_code}" && echo " ✅" || echo " ❌"

# Check buyer
echo -n "Buyer endpoints: "
curl -s -X GET "$BASE/buyer/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -o /dev/null -w "%{http_code}" && echo " ✅" || echo " ❌"

# Check seller
echo -n "Marketplace endpoints: "
curl -s -X GET "$BASE/marketplace-accounts" \
  -H "Authorization: Bearer $TOKEN" \
  -o /dev/null -w "%{http_code}" && echo " ✅" || echo " ❌"

# Check pricing
echo -n "Pricing endpoints: "
curl -s -X GET "$BASE/seller/pricing/categories" \
  -o /dev/null -w "%{http_code}" && echo " ✅" || echo " ❌"

echo "===================="
echo "Status check complete!"
```

---

## Category Path Reference

For pricing endpoints, use URL-encoded category paths:

```
furniture>sofas        → furniture%3Esofas
furniture>desks        → furniture%3Edesks
furniture>tables       → furniture%3Etables
electronics>phones     → electronics%3Ephones
electronics>laptops    → electronics%3Elaptops
home>decor             → home%3Edecor
home>lighting          → home%3Elighting
```

Example:
```bash
curl -X GET "$BASE/seller/pricing/stats?category=furniture%3Esofas" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Valid Enum Values

**Notification Frequencies:**
- `instant`
- `daily_digest`
- `weekly_digest`

**Item Conditions:**
- `new`
- `like_new`
- `good`
- `fair`
- `poor`

**Marketplace Platforms:**
- `ebay`
- `facebook`
- `etsy`
- `craigslist`
- `shopify`

**Snap Status:**
- `pending`
- `processing`
- `ready`
- `published`
- `failed`

---

## Debug Tips

### See Full Response
```bash
curl -v -X GET "$BASE/buyer/deals" \
  -H "Authorization: Bearer $TOKEN"
```

### Format JSON Output
```bash
curl -s -X GET "$BASE/buyer/deals" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### Check Only Status Code
```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X GET "$BASE/buyer/deals" \
  -H "Authorization: Bearer $TOKEN"
```

### See Request Headers Sent
```bash
curl -v -X GET "$BASE/buyer/deals" \
  -H "Authorization: Bearer $TOKEN" 2>&1 | grep ">"
```

### See Response Headers
```bash
curl -i -X GET "$BASE/buyer/deals" \
  -H "Authorization: Bearer $TOKEN"
```

### Decode JWT Token
```bash
# Your token looks like: eyJhbGciOi...
# Paste at: https://jwt.io
# Or decode with:
echo "your_token_here" | cut -d'.' -f2 | base64 -d | python -m json.tool
```

---

## One-Liner Tests

### Test auth works
```bash
curl -s -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" -d '{"username":"test_'$(date +%s)'","email":"t@example.com","password":"Pass123"}' | grep access_token
```

### Test endpoint is reachable
```bash
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:8000/buyer/deals -H "Authorization: Bearer $TOKEN"
```

### Count returned deals
```bash
curl -s -X GET "http://localhost:8000/buyer/deals" -H "Authorization: Bearer $TOKEN" | grep -o '"id"' | wc -l
```

### Get first deal ID
```bash
curl -s -X GET "http://localhost:8000/buyer/deals" -H "Authorization: Bearer $TOKEN" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2
```

---

## Most Common Mistakes

| Problem | Solution |
|---------|----------|
| "Not authenticated" | Missing or invalid token - use `python mint_jwt_tokens.py` |
| "Seller access required" | Using buyer token on seller endpoint - use `--seller` flag |
| "Connection refused" | Backend not running - `docker compose up -d` |
| Invalid frequency value | Use: instant, daily_digest, or weekly_digest |
| 404 on marketplace account | ID doesn't exist - list accounts first with GET |
| Duplicate platform error | User already has account for that platform |
| Invalid JSON in request | Check quotes and escaping in curl command |
| Category not found | Use format `furniture%3Esofas` not `furniture>sofas` |

---

**Need more? See:**
- `PHASE_4_TESTING_GUIDE.md` - Detailed endpoint reference
- `PHASE_4_TEST_PASSES.md` - Step-by-step workflows
- `TESTING_QUICK_START.md` - Quick reference
