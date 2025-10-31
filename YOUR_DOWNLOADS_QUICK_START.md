# Your Downloads - Quick Start Guide

You downloaded two testing files. Here's exactly how to use them.

---

## 📂 What You Downloaded

From `E:\downloads\`:

1. **Deal-Scout-Phase4.postman_collection.json**
   - Complete Postman collection with all endpoints
   - Pre-configured with your actual API schema
   - Ready to import and use

2. **deal-scout-phase4.http**
   - VS Code REST Client file
   - All endpoints ready to test inline
   - Ready to open in VS Code

---

## 🚀 Method 1: Postman (Recommended - Easiest)

### Step 1: Import Collection
1. Open Postman
2. Click **Import** (top left)
3. Choose **Files**
4. Select: `Deal-Scout-Phase4.postman_collection.json`
5. Collection appears in left sidebar

### Step 2: Set Variables
1. Find **Environments** dropdown (top right area)
2. Create new environment or use default
3. Set these variables:
   - `base_url` = `http://localhost:8000`
   - `token` = **(get from next step)**

### Step 3: Get JWT Token
Option A (quickest):
```bash
python mint_jwt_tokens.py --buyer
# Copy the token output
# Paste into Postman {{token}} variable
```

Option B (from API):
```bash
# Run the /auth/register or /auth/login endpoint
# Copy access_token from response
# Paste into Postman {{token}} variable
```

### Step 4: Start Testing
1. In Postman, click on any folder (Buyer, Seller, etc.)
2. Click on any request
3. Click **Send**
4. See response in panel below

---

## 🚀 Method 2: VS Code REST Client (Fastest for Developers)

### Step 1: Install Extension
1. Open VS Code
2. Go to Extensions
3. Search: "REST Client"
4. Install the one by **Huachao Mao**
5. Reload VS Code

### Step 2: Open File
1. Open `E:\downloads\deal-scout-phase4.http`
2. You'll see requests like:
```
### List deals
GET {{base_url}}/buyer/deals?category=Furniture&min_score=7
Authorization: Bearer {{token}}
```

### Step 3: Set Token
1. At the top of the file, find:
```
@token = REPLACE_WITH_JWT
```

2. Replace with your actual token:
```
@token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...
```

3. Get token from:
```bash
python mint_jwt_tokens.py --buyer
# Copy the output
```

### Step 4: Send Requests
1. Hover over any request (like "### List deals")
2. You'll see "Send Request" link appear above the request
3. Click it
4. Response appears in right panel

---

## 🔑 Getting Your JWT Token (Important!)

### Quickest Way
```bash
cd "C:\Users\darne\OneDrive\Documents\Python Scripts\2WayMarketAssistant\deal-scout"
python mint_jwt_tokens.py --buyer
```

**Output will look like:**
```
======================================================================
✅ TOKEN GENERATED FOR: BUYER
======================================================================

Token Payload:
{
  "user_id": 1,
  "username": "testbuyer",
  "email": "buyer@example.com",
  "role": "buyer",
  ...
}

Token (for use in headers):
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjox...
```

**Copy the long token string** (everything after "Bearer ") and paste it into:
- Postman: `{{token}}` variable
- VS Code: `@token = ...` line

### Alternative: From Your API
```bash
# If you have an /auth/login or /auth/register endpoint:
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"testuser_'$(date +%s)'",
    "email":"test'$(date +%s)'@example.com",
    "password":"TestPassword123"
  }'

# Copy the "access_token" value from the response
```

---

## ⚡ Start Backend First

```bash
docker compose up -d
```

Wait for it to start (takes 5-10 seconds), then you can test.

---

## 📋 Testing Workflow with Your Files

### Scenario 1: Testing Buyer Flow
**Using your Postman collection:**

1. Postman → Buyer folder → List deals → Send
2. Copy a listing_id from response
3. Postman → Buyer folder → Save a deal → Set {{listing_id}} variable → Send
4. Postman → Buyer folder → Saved deals → Send (should show the deal you saved)
5. Postman → Buyer folder → Update preferences → Edit body → Send

**Expected:** All return 200 or 201

---

### Scenario 2: Testing Seller Snap Flow
**Using your REST Client file:**

1. VS Code → Find "### Create snap job"
2. Edit @job_id variable or use placeholder
3. Click "Send Request"
4. Copy job_id from response
5. Find "### Get snap status"
6. Replace @job_id with the one from step 4
7. Click "Send Request"
8. Find "### Publish snap"
9. Click "Send Request"

**Expected:** All return 200 or 201

---

## 🧪 Quick Test (All Folders)

Use Postman's **Run Collection** feature to test all endpoints:

1. Right-click collection in sidebar
2. Click **Run**
3. Postman opens test runner
4. Click **Run [Collection Name]**
5. Watch all requests execute
6. See pass/fail summary at end

---

## 🔍 Debugging Failed Requests

### In Postman:
1. Click the failed request
2. Look at **Response** tab (bottom)
3. Check:
   - Status code (should be 200, 201, or 4xx with message)
   - Error message
   - Headers

### In VS Code REST Client:
1. Request failed? Check right panel
2. Look for HTTP status code
3. Read error message
4. Check token is valid
5. Check URL is correct

### Common Issues:

| Error | Fix |
|-------|-----|
| 401 Unauthorized | Token missing or invalid. Run `python mint_jwt_tokens.py --buyer` |
| 403 Forbidden | Using wrong role. Use `--seller` flag if testing seller endpoints |
| 404 Not Found | Resource doesn't exist. Use valid IDs from GET requests |
| Connection refused | Backend not running. Run `docker compose up -d` |
| 422 Unprocessable | Invalid request body. Check field names and types |

---

## 📝 Field Name Reference

Your files use these field names (important for requests):

```
Buyer endpoints:
  listing_id       (the deal ID)
  status           (e.g., "unread" for notifications)
  radius_mi        (search radius in miles)
  min_condition    (e.g., "good")
  keywords_include (list of keywords)
  notify_channels  (e.g., ["email"])

Seller endpoints:
  job_id           (snap job ID)
  marketplaces     (list, e.g., ["ebay"])
  price_cents      (price in cents, e.g., 4500 = $45)

Marketplace endpoints:
  marketplace      (e.g., "ebay", "facebook")
  display_name     (name for the account)
  account_id       (ID of marketplace account)

Notification endpoints:
  channels         (list, e.g., ["email", "discord"])
  frequency        (e.g., "instant")
  min_deal_score   (0-10)
```

**When editing requests in Postman/REST file, use these exact field names.**

---

## ✅ Example: Complete Buyer Test

**Using Postman:**

### Request 1: List Deals
```
Folder: Buyer
Request: List deals
Click Send
Response: Array of deals
```

### Request 2: Save Deal
```
Folder: Buyer
Request: Save a deal
Edit {{listing_id}} = (copy an ID from previous response)
Click Send
Response: 200 OK
```

### Request 3: View Saved
```
Folder: Buyer
Request: Saved deals
Click Send
Response: Array including the deal from Request 2
```

### Request 4: Update Preferences
```
Folder: Buyer
Request: Update preferences
Edit body:
{
  "radius_mi": 50,
  "min_condition": "good",
  "keywords_include": ["couch"],
  "notify_channels": ["email"]
}
Click Send
Response: 200 OK
```

**Result:** Buyer flow works! ✅

---

## 🧯 Error Testing

**Test that your API correctly returns errors:**

### 401 Unauthorized
```
Postman: Any request → Remove {{token}} variable → Send
Expected: 401 with error message
```

### 403 Forbidden
```
Postman: Seller endpoint (like Create snap)
With buyer token
Expected: 403 with error message
```

### 404 Not Found
```
Postman: Any GET with ID
Use non-existent ID (like 99999)
Expected: 404 with error message
```

### 409 Conflict
```
Postman: Marketplace Accounts → Create account
Create same marketplace twice
Expected: 409 with error message
```

### 422 Unprocessable
```
Postman: Any endpoint
Send invalid data (wrong field type, missing required field)
Expected: 422 with field errors
```

---

## 📚 Need More Help?

### For Test Procedures:
- See: `PHASE_4_TEST_PASSES.md` (step-by-step for all 5 passes)

### For Field Mapping:
- See: `TESTING_INTEGRATION_GUIDE.md` (maps your schema to documentation)

### For Quick Commands:
- See: `TESTING_CHEAT_SHEET.md` (curl examples and patterns)

### For Overall Testing:
- See: `README_PHASE4_TESTING.md` (navigation guide)

---

## 🎯 Success Criteria

After testing with your downloaded files, you should have:

- ✅ Generated at least one JWT token
- ✅ Successfully ran 5+ requests with 2xx responses
- ✅ Verified error handling (got 401, 403, 404, 422 appropriately)
- ✅ Tested full buyer flow (list → save → unsave → update prefs)
- ✅ Tested seller flow (create snap → publish)
- ✅ Verified database persistence (saved data appears on retrieval)

**All passing?** Phase 4 testing complete! ✅

---

## ⚡ One-Minute Setup

```bash
# 1. Start backend
docker compose up -d

# 2. Generate token
python mint_jwt_tokens.py --buyer

# 3. Postman: Import Deal-Scout-Phase4.postman_collection.json
#    Set {{token}} = your token from step 2

# 4. Click "Run Collection"
# 5. Watch all endpoints test automatically

# Done! Check results.
```

---

## 🎉 You're Ready!

You have:
1. ✅ Your Postman collection (with real endpoints)
2. ✅ Your REST Client file (with real requests)
3. ✅ JWT token generator
4. ✅ Step-by-step test procedures
5. ✅ Edge case testing guide

**Start with Postman or VS Code REST Client above, then follow the test procedures in `PHASE_4_TEST_PASSES.md` for comprehensive testing.**

Happy testing! 🚀
