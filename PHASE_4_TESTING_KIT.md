# Phase 4 Testing Kit - Complete Guide

Everything you need to test all 37 Phase 4 endpoints right away. Choose your preferred testing method and start verifying.

---

## Quick Navigation

| Need | File | Use When |
|------|------|----------|
| **Interactive Testing** | Swagger UI | You want a visual interface with no setup |
| **Postman** | `Deal-Scout-Phase4.postman_collection.json` | You prefer GUI testing, API debugging, team sharing |
| **VS Code** | `deal-scout-phase4.http` | You live in VS Code and want inline testing |
| **Python** | `test_phase4_api.py` | You want automated verification |
| **Token Generator** | `mint_jwt_tokens.py` | You need quick JWT tokens for testing |
| **Test Workflows** | `PHASE_4_TEST_PASSES.md` | You want step-by-step test procedures |
| **Troubleshooting** | `TESTING_QUICK_START.md` | You need help with common issues |

---

## Option 1: Interactive Swagger UI (Easiest - No Setup)

### The Easiest Way
```bash
# 1. Make sure backend is running
docker compose up -d

# 2. Open browser
http://localhost:8000/docs

# Done! You see the interactive interface
```

### What You Get
- Beautiful interactive interface
- Click "Try it out" on any endpoint
- Authorize once with your JWT token (lock icon at top)
- See live responses instantly
- No command line needed

### Step-by-Step
1. Open http://localhost:8000/docs
2. Click lock icon (🔒) at top right
3. Paste your JWT token in "Authorization" field
4. Click "Authorize" and "Close"
5. Expand any endpoint
6. Click "Try it out"
7. Modify parameters if needed
8. Click "Execute"
9. See response immediately

---

## Option 2: Postman Collection (Best for Teams)

### Import Collection
1. Download or open Postman
2. Click "Import" button
3. Select `Deal-Scout-Phase4.postman_collection.json`
4. Collection appears in left sidebar with all folders

### What's Included
- All 37 endpoints organized in 9 logical folders
- Pre-configured request bodies with sample data
- Environment variables for `{{base_url}}` and `{{token}}`
- Error testing scenarios
- Comments explaining each request

### First Test
1. Get token: Run `/auth/register` endpoint
2. Copy `access_token` from response
3. Click "Environment" (top right) → Select "Phase 4 API"
4. Paste token into `token` variable
5. Run any endpoint - token will be auto-filled

### Organizing Your Testing
- Each folder groups related endpoints
- Folders: Authentication, Buyer (Deals), Buyer (Notifications), Buyer (Preferences), Marketplace Accounts, Snap Studio, Pricing, Error Testing
- Run folder tests sequentially for complete workflow

### Tips
- Use folder "Run" feature to test all endpoints in a category at once
- Check "Tests" tab for built-in validation scripts
- Use "Pre-request Script" for dynamic data generation

---

## Option 3: VS Code REST Client (Fastest for Developers)

### Installation
1. Install extension: "REST Client" by Huachao Mao
2. Open `deal-scout-phase4.http`

### Usage
1. Set `@token` variable to your JWT token
2. Hover over any request → "Send Request" appears
3. Click "Send Request"
4. Response appears in side panel
5. Repeat for other endpoints

### What's Included
- 46 pre-written requests covering all 37 endpoints
- Variables for base URL and token
- Test flows grouped with comments
- Error testing scenarios

### Quick Test Flow
1. Register user: Run `/auth/register` request
2. Copy token from response
3. Paste into `@token = ...` at top of file
4. Run any authenticated request
5. Response appears instantly in side panel

### Pro Tips
- Use `Ctrl+Alt+R` to send request
- View response in side panel without leaving editor
- Chain requests using variables in responses
- Generate sample data with `{{$randomInt}}` variables

---

## Option 4: Python Automated Testing

### One-Command Test
```bash
python test_phase4_api.py
```

### What It Tests
✅ User registration
✅ Buyer deals endpoints
✅ Notification preferences
✅ Marketplace accounts
✅ Snap studio
✅ Pricing endpoints
✅ All with proper error handling

### Output
```
============================================================
PHASE 4 API TESTING
============================================================

[1] REGISTERING TEST USER...
OK: User registered! ID: 6
    Token (first 20 chars): eyJhbGciOiJIUzI1NiIs...

[2] TESTING BUYER DEALS ENDPOINT...
OK: Got 3 deals
    First deal: Leather Couch ($1200)

[3] TESTING NOTIFICATION PREFERENCES...
OK: Got preferences
    Email notifications: true
    Frequency: daily_digest

... (more tests)

============================================================
SUCCESS: PHASE 4 TESTING COMPLETE!
============================================================
```

### Running Custom Tests
You can modify `test_phase4_api.py` to test specific endpoints:

```python
# In test_phase4_api.py, add your custom test:
response = requests.get(
    f"{BASE_URL}/buyer/deals?category=furniture",
    headers=headers,
    timeout=5
)
print(f"Status: {response.status_code}")
print(f"Data: {response.json()}")
```

---

## Token Generation Helper

### Quick Token Generation
```bash
# Interactive menu
python mint_jwt_tokens.py

# Generate buyer token
python mint_jwt_tokens.py --buyer

# Generate seller token
python mint_jwt_tokens.py --seller

# Custom token
python mint_jwt_tokens.py --user 5 --username testuser --role seller
```

### What It Does
- Generates valid JWT tokens instantly
- No need to register users first
- Supports buyer, seller, and admin roles
- Can decode existing tokens for debugging

### Output Example
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
  "exp": "...",
  "iat": "..."
}

Token (for use in headers):
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

To use in VS Code REST Client:
@token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Expires in: 24 hours
======================================================================
```

---

## Test Pass Documentation

### What Are Test Passes?
Step-by-step instructions for complete workflows, organized by feature.

### Available Passes
1. **Test Pass A**: Buyer Flow (5 min)
   - Register, browse deals, save/unsave, manage preferences

2. **Test Pass B**: Seller Snap (5 min)
   - Create marketplace accounts, snap jobs, publish to multiple platforms

3. **Test Pass C**: Marketplace Management (3 min)
   - Complete CRUD operations on marketplace accounts

4. **Test Pass D**: Notification Preferences (3 min)
   - Configure notification settings, channels, frequencies

5. **Test Pass E**: Pricing & Analytics (3 min)
   - View market trends, price statistics, create comparables

6. **Edge Cases**: Comprehensive edge case testing
   - 401/403/404/409/422 error scenarios
   - Validation boundaries
   - Authorization testing

### How to Use
1. Open `PHASE_4_TEST_PASSES.md`
2. Choose a test pass
3. Follow step-by-step instructions
4. Copy curl examples or use them as reference for Postman/REST Client
5. Check off completion

### Estimated Time
- All test passes: ~20 minutes
- Single pass: 2-5 minutes each
- Edge cases: 10 minutes

---

## Complete Testing Workflow

### Minute 0-1: Preparation
```bash
# Start backend
docker compose up -d

# Open Swagger UI
open http://localhost:8000/docs
```

### Minute 1-5: Quick Smoke Test
**Use any method:**
- Swagger UI: Click through 5 endpoints
- Postman: Run "Authentication" folder
- VS Code: Run auth requests
- Python: `python test_phase4_api.py`

### Minute 5-20: Full Test Passes
- Run Test Pass A (Buyer)
- Run Test Pass B (Seller)
- Run Test Pass C (Marketplace)
- Run Test Pass D (Notifications)
- Run Test Pass E (Pricing)

### Minute 20-30: Edge Case Testing
- Run EC1-EC7 scenarios from `PHASE_4_TEST_PASSES.md`
- Verify 401/403/404/409/422 handling
- Test boundary conditions

### Minute 30+: Load Testing (Optional)
```bash
# Light load test
bash test_load.sh   # macOS/Linux

# Or PowerShell
./test_load.ps1     # Windows
```

---

## Choosing Your Testing Method

### Use **Swagger UI** if:
- ✅ You just want to verify endpoints work
- ✅ You don't want to install anything
- ✅ You like visual interfaces
- ✅ You want zero command line

### Use **Postman** if:
- ✅ You need to share tests with team
- ✅ You want test automation/assertions
- ✅ You're debugging complex workflows
- ✅ You want to run tests in CI/CD

### Use **VS Code REST Client** if:
- ✅ You live in VS Code
- ✅ You want inline testing during development
- ✅ You prefer plain text over GUI
- ✅ You want quick request/response cycles

### Use **Python Script** if:
- ✅ You want fully automated testing
- ✅ You need CI/CD integration
- ✅ You want to test many endpoints rapidly
- ✅ You need custom validation logic

### Use **Token Generator** if:
- ✅ You need to test different user roles quickly
- ✅ You want tokens without registering
- ✅ You're testing role-based access control
- ✅ You need to debug JWT issues

### Use **Test Passes** if:
- ✅ You want step-by-step workflows
- ✅ You need documentation of what to test
- ✅ You want to understand complete user journeys
- ✅ You're verifying edge cases

---

## Files You Have

```
deal-scout/
├── PHASE_4_TESTING_KIT.md                    ← You are here
├── PHASE_4_TESTING_GUIDE.md                  ← Detailed endpoint reference
├── TESTING_QUICK_START.md                    ← Quick reference
├── PHASE_4_TEST_PASSES.md                    ← Step-by-step workflows
├── Deal-Scout-Phase4.postman_collection.json ← Postman collection
├── deal-scout-phase4.http                    ← VS Code REST Client
├── mint_jwt_tokens.py                        ← Token generator
├── test_phase4_api.py                        ← Python test script
└── test_load.sh                              ← Load testing script
```

---

## Troubleshooting

### "Connection refused"
```bash
# Backend not running
docker compose up -d
docker compose logs -f api  # View logs
```

### "Invalid authentication credentials"
```bash
# Token missing or expired
python mint_jwt_tokens.py --buyer  # Generate new token

# For auth/register endpoint:
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Pass123"}'
```

### "403 Forbidden - Seller access required"
- You're using a buyer token on a seller endpoint
- Use `python mint_jwt_tokens.py --seller` to get seller token

### "404 Not Found"
- Wrong endpoint path or resource ID doesn't exist
- Check endpoint paths in `PHASE_4_TESTING_GUIDE.md`

### "422 Unprocessable Entity"
- Invalid request data
- Check parameter validation in response message
- Review `PHASE_4_TEST_PASSES.md` EC3 section

### Postman Collection Won't Import
1. Download file again
2. Make sure file is `.json` format
3. Try "Paste Raw Text" instead of "Import File"

### VS Code REST Client Not Sending
1. Install extension: "REST Client" by Huachao Mao
2. Restart VS Code
3. Check `.http` file syntax

---

## Next Steps After Testing

1. ✅ Run all test passes
2. ✅ Verify edge cases pass
3. ✅ Check error handling is correct
4. ✅ Review response formats match documentation
5. ✅ Proceed to Phase 5 development

---

## Summary

You have everything to test Phase 4:

| Task | Tool | Time |
|------|------|------|
| Browse/test endpoints | Swagger UI | 5 min |
| Quick automated test | Python script | 5 min |
| Complete workflows | Test Passes | 20 min |
| GUI-based testing | Postman | 10 min |
| Inline VS Code testing | REST Client | 10 min |
| Error scenario testing | Test Passes + Postman | 10 min |
| Load testing | test_load.sh | 5 min |

**Total time to fully test: ~30-45 minutes**

Pick your method and start testing! 🚀

---

## Quick Links

- **Running Backend**: `docker compose up -d`
- **Swagger UI**: http://localhost:8000/docs
- **API Docs**: http://localhost:8000/openapi.json
- **Generate Token**: `python mint_jwt_tokens.py`
- **Run Tests**: `python test_phase4_api.py`
- **Detailed Guide**: See `PHASE_4_TESTING_GUIDE.md`

---

**Happy Testing! 🎉**
