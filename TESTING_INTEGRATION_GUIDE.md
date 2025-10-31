# Testing Integration Guide

**Bridge between your actual API schema and the comprehensive testing documentation**

This guide maps the actual Postman and REST Client files (from your downloads) to the testing procedures in this directory.

---

## 📌 Important Note

You have **TWO sets** of testing resources:

| Source | What It Is | How to Use |
|--------|-----------|-----------|
| **Your Downloads** | Actual Postman/REST files with real endpoint schemas | Use these for actual testing |
| **This Directory** | Comprehensive procedures, guides, and edge case documentation | Follow these for test workflows |

**Best Approach:** Use your downloaded files for requests, use this directory for procedures and guidance.

---

## 🔄 Schema Mapping

### Your Actual Field Names vs Documentation References

#### Buyer Deals Endpoint
```
Your API:
  GET /buyer/deals?category=Furniture&min_score=7&max_price=200

Documentation references:
  category, min_score, max_price (✓ same)
```

#### Save Deal Endpoint
```
Your API:
  POST /buyer/deals/{{listing_id}}/save

Documentation references:
  /buyer/deals/{id}/save (✓ compatible, just parameter naming)
```

#### Update Preferences
```
Your API body:
  {
    "radius_mi": 50,
    "min_condition": "good",
    "keywords_include": ["couch"],
    "notify_channels": ["email"]
  }

Documentation references:
  search_radius_mi, preferred_condition, notification_enabled
  (⚠️ field names differ - use YOUR schema when testing)
```

#### Snap Job
```
Your API:
  POST /seller/snap { "note": "testing" }

Documentation references:
  { "photos": [...], "notes": "...", "source": "..." }
  (⚠️ different schema - use YOUR structure)
```

#### Publish Snap
```
Your API:
  POST /seller/snap/{{job_id}}/publish
  { "marketplaces": ["ebay"], "price_cents": 4500 }

Documentation references:
  POST /seller/snap/{id}/publish
  { "title": "...", "description": "...", "platforms": [...] }
  (⚠️ different request body - adjust for your schema)
```

---

## 🚀 How to Test Using Both Resources

### Step 1: Choose Testing Method

**Option A: Postman (Recommended)**
- File: `E:\downloads\Deal-Scout-Phase4.postman_collection.json`
- Import into Postman
- Set variables: `{{base_url}}` and `{{token}}`
- Endpoints are pre-configured with YOUR actual schema

**Option B: VS Code REST Client**
- File: `E:\downloads\deal-scout-phase4.http`
- Install REST Client extension
- Edit `@token` at top
- All requests use YOUR actual field names

**Option C: Follow Documentation Procedures**
- Use `PHASE_4_TEST_PASSES.md` for step-by-step workflows
- Adapt field names/request bodies to YOUR schema
- Use your Postman or REST files as reference for actual syntax

---

## 📋 Test Pass A - Buyer Flow

### Procedure (from PHASE_4_TEST_PASSES.md)
1. Register user → Get JWT token
2. Browse deals with filters
3. Save a deal
4. View saved deals
5. Unsave deal
6. Update preferences
7. Check preferences were updated

### Actual Implementation (Using YOUR Files)

**1. Register & Get Token**
```bash
# Use your auth/register endpoint
# Copy the token from response
```

**2. List Deals with Filters**
```
Your Postman collection → Buyer → List deals
Runs: GET /buyer/deals?category=Furniture&min_score=7&max_price=200
✓ Should return array of deals
```

**3. Save a Deal**
```
Your Postman collection → Buyer → Save a deal
Update {{listing_id}} variable with a deal ID from step 2
Runs: POST /buyer/deals/{{listing_id}}/save
✓ Should return 200/201
```

**4. View Saved Deals**
```
Your Postman collection → Buyer → Saved deals
Runs: GET /buyer/deals/saved
✓ Should include the deal saved in step 3
```

**5. Unsave Deal**
```
Your Postman collection → Buyer → [endpoint for unsave if exists]
Or: DELETE /buyer/deals/{{listing_id}}/save
✓ Should return 200
```

**6. Update Preferences**
```
Your Postman collection → Buyer → Update preferences
Your body schema:
{
  "radius_mi": 50,
  "min_condition": "good",
  "keywords_include": ["couch", "kitchen island"],
  "notify_channels": ["email"]
}
✓ Should return 200
```

**7. Verify Update**
```
Your Postman collection → Buyer → Get preferences
Verify returned data matches step 6 updates
```

---

## 📋 Test Pass B - Seller Snap & Publish

### Procedure (from PHASE_4_TEST_PASSES.md)
1. Register as seller
2. Create marketplace accounts
3. Create snap job
4. Get snap job status
5. Publish snap to marketplaces

### Actual Implementation (Using YOUR Files)

**1. Register Seller Account**
```bash
# Use auth/register with seller credentials
# Copy JWT token
```

**2. Create Marketplace Accounts**
```
Your Postman collection → Marketplace Accounts → Create account
Request body (adapt to your schema):
{
  "marketplace": "ebay",
  "display_name": "Primary eBay"
}
✓ Should return 201
```

**3. Create Snap Job**
```
Your Postman collection → Seller → Create snap job
Your body schema:
{
  "note": "testing"
}
✓ Should return 201 with job_id
Copy job_id to {{job_id}} variable
```

**4. Get Snap Status**
```
Your Postman collection → Seller → Get snap status
Runs: GET /seller/snap/{{job_id}}
✓ Should return job details
```

**5. Publish Snap**
```
Your Postman collection → Seller → Publish snap
Your body schema:
{
  "marketplaces": ["ebay"],
  "price_cents": 4500
}
✓ Should return 201 with CrossPost record
```

---

## 📋 Test Pass C - Marketplace Account CRUD

### Procedure Summary
Create → List → Get → Update → Disconnect → Reconnect → Delete

### Actual Implementation

**Check your Postman collection's "Marketplace Accounts" folder for all 7 endpoints:**
1. POST /marketplace-accounts (create)
2. GET /marketplace-accounts (list)
3. GET /marketplace-accounts/{id} (get)
4. PATCH /marketplace-accounts/{id} (update)
5. POST /marketplace-accounts/{id}/disconnect (disconnect)
6. POST /marketplace-accounts/{id}/reconnect (reconnect)
7. DELETE /marketplace-accounts/{id} (delete)

**Expected flow:**
- Step 1 returns 201 with account_id
- Steps 2-5 return 200
- Step 6 should work if account was disconnected
- Step 7 should return 200 or 204

---

## 📋 Test Pass D - Notification Preferences

### Procedure Summary
Get → Update → Reset → History → Mark All Read → Clear

### Actual Implementation

**Check your Postman collection's "Notification Preferences" folder for:**
1. GET /notification-preferences
2. PUT /notification-preferences
3. POST /notification-preferences/reset (or similar)
4. GET /notification-preferences/history
5. POST /notification-preferences/mark-all-read
6. POST /notification-preferences/clear

**Update request body (adapt to your schema):**
```json
{
  "channels": ["email", "discord"],
  "frequency": "instant",
  "min_deal_score": 7
}
```

---

## 📋 Test Pass E - Pricing & Analytics

### Procedure Summary
Categories → Stats → Trends → Your Items → Create Comp

### Actual Implementation

**Check your Postman collection's "Pricing" folder:**
1. GET /seller/pricing/categories
2. GET /seller/pricing/stats?category=Furniture&condition=good
3. GET /seller/pricing/market-trends?category=Furniture&days=90
4. GET /seller/pricing/my-items
5. POST /seller/pricing/comps (create comparable)

---

## 🧯 Edge Case Testing

Use `PHASE_4_TEST_PASSES.md` edge case section but **adjust expected responses to your actual API**:

### EC1: Missing Auth Header
```bash
GET /buyer/deals (no Authorization header)
Expected: 401 Unauthorized with your error schema
```

### EC2: Invalid Token
```bash
GET /buyer/deals
Authorization: Bearer invalid_token
Expected: 401 Unauthorized
```

### EC3: RBAC - Buyer on Seller Endpoint
```bash
POST /seller/snap (with buyer token)
Expected: 403 Forbidden or 401 depending on your impl
```

### EC4: Not Found
```bash
GET /buyer/deals/999999/save (non-existent listing)
Expected: 404 Not Found
```

### EC5: Conflict (Duplicate)
```bash
POST /marketplace-accounts (same platform twice)
Expected: 409 Conflict or 422 depending on your validation
```

### EC6: Validation (422)
```bash
PUT /notification-preferences?invalid_frequency=xyz
Expected: 422 Unprocessable Entity with field errors
```

---

## 🔌 Token Generation

### Using Your Python Script (if available)
```bash
python mint_jwt_tokens.py --buyer
```

### OR Manual JWT Creation
```python
import jwt, time, uuid

secret = "YOUR_JWT_SECRET"  # From .env
user_id = str(uuid.uuid4())  # New user UUID
claims = {
    "sub": user_id,
    "exp": int(time.time()) + 2*60*60,  # 2 hours
    "roles": ["buyer", "seller"]  # Include both for testing
}
token = jwt.encode(claims, secret, algorithm="HS256")
print(token)  # Paste into {{token}}
```

---

## 📝 Field Name Differences Summary

### Your Schema vs Documentation References

| Your Postman/REST File | Documentation Example | Actual API Field |
|------------------------|----------------------|------------------|
| listing_id | id/deal_id | Depends on API |
| job_id | snap_id/job_id | Your naming |
| account_id | marketplace_account_id | Your naming |
| notification_id | notification_id | Your naming |
| status=unread | is_read boolean | Your schema |
| radius_mi | search_radius_mi | Your naming |
| notify_channels | notification_channels | Your naming |
| price_cents | price (in dollars) | Your units |
| note | notes | Your naming |
| marketplace | platform | Your naming |

**Key point:** When following test procedures, always use YOUR field names from the Postman/REST files.

---

## ✅ Verification Using Your Files

### Quick Smoke Test (Using Your Postman Collection)
1. Open Postman
2. Import `Deal-Scout-Phase4.postman_collection.json`
3. Set `{{base_url}}` = http://localhost:8000
4. Set `{{token}}` = your JWT
5. Run each folder's requests in order:
   - ✅ Buyer folder (all 200s)
   - ✅ Seller folder (all 200s)
   - ✅ Marketplace Accounts folder (201s for create, 200s for others)
   - ✅ Notification Preferences folder (all 200s)
   - ✅ Pricing folder (all 200s)

### Error Testing (Using Your Postman Collection)
1. Remove `{{token}}` or use invalid token
2. Send any authenticated request → Expect 401
3. Use buyer token on seller endpoint → Expect 403 or 401
4. Reference non-existent ID → Expect 404
5. Create duplicate marketplace account → Expect 409 or 422
6. Send invalid enum value → Expect 422

---

## 📚 Using Both Resources Together

### Workflow:
1. **Read** `PHASE_4_TEST_PASSES.md` (understand what to test)
2. **Open** your Postman collection or REST file (actual endpoints/schemas)
3. **Adapt** the procedure to your field names
4. **Execute** the requests
5. **Verify** against expected outcomes

### Example:
```
Documentation says:
  "GET /buyer/deals?category=furniture&min_score=7"

Your REST file has:
  "GET {{base_url}}/buyer/deals?category=Furniture&min_score=7"

What you do:
  ✓ Use your REST file's exact syntax
  ✓ Follow the TEST PASS procedure for "what to check"
  ✓ Both aligned!
```

---

## 🎯 Quick Reference

### Files to Have Open During Testing

**Left Monitor/Tab:**
- `PHASE_4_TEST_PASSES.md` - What you're testing

**Middle Monitor/Tab:**
- Your Postman collection OR `deal-scout-phase4.http` - How you're testing

**Right Monitor/Tab:**
- Backend logs: `docker compose logs -f api` - Debugging

### Command to Start Everything
```bash
docker compose up -d
# Wait 5 seconds
python mint_jwt_tokens.py --buyer  # Get token
# Copy token to Postman {{token}} variable
# Open your Postman collection
# Start testing!
```

---

## 📞 If Documentation Doesn't Match Your API

**This is expected.** Your actual API may have:
- Different field names (mapping provided above)
- Different HTTP status codes (adapt to yours)
- Different error response schemas (check actual responses)
- Different validation rules (test your validation)

**Solution:** When in doubt, check your Postman collection first (it has your real schema), then adjust test procedures accordingly.

---

## ✅ Final Checklist

Before declaring Phase 4 testing complete:

- [ ] All 37 endpoints respond (check your Postman folder count)
- [ ] Authentication works (401 without token, 200 with token)
- [ ] RBAC works (403 for unauthorized roles)
- [ ] Buyer flow complete (Test Pass A)
- [ ] Seller snap flow complete (Test Pass B)
- [ ] Marketplace CRUD works (Test Pass C)
- [ ] Notification prefs work (Test Pass D)
- [ ] Pricing endpoints respond (Test Pass E)
- [ ] Error handling correct (401/403/404/409/422)
- [ ] Database persists data (create and retrieve)

---

## 🎉 You Now Have

1. **Your actual Postman collection** with real endpoint schemas
2. **Your actual REST Client file** with real field names
3. **Comprehensive documentation** with test procedures
4. **This mapping guide** to connect them

**Start testing:** Open your Postman collection, follow `PHASE_4_TEST_PASSES.md` procedures, adapt field names as needed.

**Questions about field differences?** Check this document's schema mapping section.

**Questions about test procedures?** See `PHASE_4_TEST_PASSES.md`.

**Questions about which tool to use?** See `PHASE_4_TESTING_KIT.md` or `README_PHASE4_TESTING.md`.

---

Happy testing! You've got everything you need. 🚀
