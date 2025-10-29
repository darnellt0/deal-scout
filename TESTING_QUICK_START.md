# Phase 4 Testing - Quick Start

## Three Ways to Test Phase 4

### Method 1: Interactive Swagger UI (Easiest)
Simply open your browser:
```
http://localhost:8000/docs
```

You'll see a beautiful interactive interface where you can:
- Click each endpoint to see details
- Click "Try it out" to test live
- Authorize with your JWT token (click lock icon at top)
- See real responses instantly
- No terminal commands needed!

---

### Method 2: Manual Testing with curl

#### Step 1: Register a User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","email":"myuser@example.com","password":"MyPassword123"}'
```

Save the `access_token` from the response.

#### Step 2: Test Any Endpoint

Replace `YOUR_TOKEN` with the token from Step 1:

**Get Deals:**
```bash
curl -X GET "http://localhost:8000/buyer/deals?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get Notifications:**
```bash
curl -X GET "http://localhost:8000/buyer/notifications" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get Buyer Preferences:**
```bash
curl -X GET "http://localhost:8000/buyer/preferences" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Create Marketplace Account:**
```bash
curl -X POST "http://localhost:8000/marketplace-accounts?platform=ebay&account_username=mystore" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get Pricing Categories:**
```bash
curl -X GET "http://localhost:8000/seller/pricing/categories"
```

---

### Method 3: Automated Testing with Python

```bash
# From deal-scout root directory:
python test_phase4_api.py
```

This will automatically:
1. Register a test user
2. Test buyer deals
3. Test notification preferences
4. Test marketplace accounts
5. Test snap studio
6. Test pricing endpoints
7. Print a summary

Expected output:
```
============================================================
PHASE 4 API TESTING
============================================================

[1] REGISTERING TEST USER...
OK: User registered! ID: 6

[2] TESTING BUYER DEALS ENDPOINT...
OK: Got 3 deals

[3] TESTING NOTIFICATION PREFERENCES...
OK: Got preferences

...and more
```

---

## All Phase 4 Endpoints

### Buyer Endpoints (Authenticated)
```
GET    /buyer/deals              - List top deals with filtering
GET    /buyer/deals/saved        - Get your saved deals
POST   /buyer/deals/{id}/save    - Save a deal
DELETE /buyer/deals/{id}/save    - Unsave a deal
GET    /buyer/notifications      - List your notifications
GET    /buyer/notifications/{id} - Get specific notification
PATCH  /buyer/notifications/{id}/mark-read - Mark as read
GET    /buyer/preferences        - Get your preferences
PUT    /buyer/preferences        - Update your preferences
```

### Notification Preferences (Authenticated)
```
GET    /notification-preferences              - Get preferences
PUT    /notification-preferences              - Update preferences
POST   /notification-preferences/reset        - Reset to defaults
GET    /notification-preferences/history      - View history
POST   /notification-preferences/clear        - Clear all
POST   /notification-preferences/mark-all-read - Mark all read
GET    /notification-preferences/channels-available
GET    /notification-preferences/frequencies-available
```

### Marketplace Accounts (Authenticated)
```
GET    /marketplace-accounts           - List accounts
GET    /marketplace-accounts/{id}      - Get account details
POST   /marketplace-accounts           - Create account
PATCH  /marketplace-accounts/{id}      - Update account
DELETE /marketplace-accounts/{id}      - Delete account
POST   /marketplace-accounts/{id}/disconnect   - Disable
POST   /marketplace-accounts/{id}/reconnect    - Enable
```

### Snap Studio (Authenticated)
```
POST   /seller/snap              - Create snap job
GET    /seller/snap/{id}         - Get snap status
GET    /seller/snap              - List snap jobs
POST   /seller/snap/{id}/publish - Publish to marketplace
```

### Pricing (Authenticated or Public)
```
GET    /seller/pricing/my-items      - Your items
GET    /seller/pricing/categories    - Available categories
GET    /seller/pricing/stats         - Price statistics
GET    /seller/pricing/market-trends - Price trends
POST   /seller/pricing/comps         - Create comparable
```

---

## Common Testing Flows

### Test 1: Become a Buyer (5 minutes)
1. Register user at `/auth/register`
2. Get token from response
3. `GET /buyer/deals` - See available deals
4. `POST /buyer/deals/1/save` - Save a deal
5. `GET /buyer/deals/saved` - View saved deals

### Test 2: Manage Preferences (3 minutes)
1. Register user
2. `GET /buyer/preferences` - See current settings
3. `PUT /buyer/preferences?search_radius_mi=25` - Update
4. `GET /notification-preferences` - Check notification settings
5. `PUT /notification-preferences?notification_frequency=daily_digest` - Update

### Test 3: Setup Seller Account (5 minutes)
1. Register user
2. `POST /marketplace-accounts?platform=ebay&account_username=mystore` - Connect platform
3. `GET /marketplace-accounts` - See connections
4. `POST /seller/snap` - Create snap job
5. `POST /seller/snap/1/publish` - Cross-post to marketplace

### Test 4: Analyze Pricing (2 minutes)
1. `GET /seller/pricing/categories` - See available categories
2. `GET /seller/pricing/stats?category=furniture%3Esofas` - Get price stats
3. `GET /seller/pricing/market-trends?category=furniture%3Esofas&days=30` - See trends

---

## Troubleshooting

### "Connection refused"
Backend not running. Fix:
```bash
docker compose up -d
```

### "Invalid authentication credentials"
Token expired or invalid. Get a new one:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","email":"new@example.com","password":"Password123"}'
```

### "Seller access required"
Your user role is "buyer". Some endpoints require seller role. This is working as expected for role-based access control.

### "404 Not Found"
The endpoint path might be wrong. Double-check spelling and structure.

---

## What to Verify

✅ Can register users
✅ Can get deals list
✅ Can save/unsave deals
✅ Can manage preferences
✅ Can create marketplace accounts
✅ Can create snap jobs
✅ Can view pricing data
✅ Authentication tokens work
✅ Authorization (role-based access) works
✅ Errors return correct status codes

---

## Next Steps

1. **Test all endpoints** using one of the three methods above
2. **Read** `PHASE_4_TESTING_GUIDE.md` for detailed examples
3. **Report any issues** with specific endpoints
4. **Proceed to Phase 5** when satisfied with Phase 4

---

## Still Have Questions?

**Full Testing Guide**: Read `PHASE_4_TESTING_GUIDE.md`

**Need Help?**: Visit `http://localhost:8000/docs` for interactive docs

**Want Examples?**: See `test_phase4_api.py` for Python testing code

---

Happy Testing! 🚀
