# Phase 4 Testing - Start Here

Everything you need to test Phase 4 endpoints is in this directory. Pick your method and start testing.

---

## 🚀 Quick Start (Pick One)

### Visual Testing (1 minute)
```bash
docker compose up -d
open http://localhost:8000/docs
# Click "Try it out" on any endpoint
```

### Python Testing (1 minute)
```bash
docker compose up -d
python test_phase4_api.py
```

### VS Code Testing (2 minutes)
```bash
# Install "REST Client" extension
# Open deal-scout-phase4.http
# Paste your JWT token into @token variable
# Click "Send Request" on any request
```

### Postman Testing (3 minutes)
```bash
# Import Deal-Scout-Phase4.postman_collection.json
# Paste token into {{token}} variable
# Start clicking "Send"
```

---

## 📚 Testing Resources

| Resource | Purpose | Time | Type |
|----------|---------|------|------|
| **PHASE_4_COMPLETE.md** | Status overview & what's done | 2 min | 📋 Summary |
| **PHASE_4_TESTING_KIT.md** | Choose your testing method | 5 min | 🗺️ Guide |
| **TESTING_QUICK_START.md** | Three ways to test | 3 min | 🚀 Quick Start |
| **PHASE_4_TESTING_GUIDE.md** | Detailed endpoint reference | 20 min | 📖 Reference |
| **PHASE_4_TEST_PASSES.md** | Step-by-step test procedures | 30 min | ✅ Procedures |
| **TESTING_CHEAT_SHEET.md** | Quick curl command reference | 5 min | 💾 Cheat Sheet |

---

## 🛠️ Tools & Scripts

| Tool | Purpose | Usage |
|------|---------|-------|
| **Swagger UI** | Interactive testing | http://localhost:8000/docs |
| **Deal-Scout-Phase4.postman_collection.json** | Postman collection | Import into Postman |
| **deal-scout-phase4.http** | VS Code REST Client | Open in VS Code + Install extension |
| **mint_jwt_tokens.py** | Generate test tokens | `python mint_jwt_tokens.py` |
| **test_phase4_api.py** | Automated test script | `python test_phase4_api.py` |

---

## 🗺️ Navigation by Need

### "I just want to test endpoints"
1. Read: `TESTING_QUICK_START.md` (3 min)
2. Choose a method (Swagger/Postman/REST/Python)
3. Start testing

### "I need step-by-step procedures"
1. Read: `PHASE_4_TEST_PASSES.md`
2. Follow Test Pass A, B, C, D, E
3. Run edge case tests
4. You're done!

### "I'm sharing with my team"
1. Export: `Deal-Scout-Phase4.postman_collection.json`
2. Share: `PHASE_4_TESTING_GUIDE.md`
3. Share: `PHASE_4_TESTING_KIT.md`

### "I need quick reference"
1. Use: `TESTING_CHEAT_SHEET.md`
2. Copy-paste curl commands
3. Edit token and endpoint IDs as needed

### "I want everything automated"
1. Run: `python test_phase4_api.py`
2. Check results
3. Done in 1 minute

### "I need comprehensive testing"
1. Read: `PHASE_4_TESTING_KIT.md` (full overview)
2. Follow: `PHASE_4_TEST_PASSES.md` (all test passes)
3. Check: Error handling and edge cases
4. Estimated time: 30-45 minutes

---

## 📋 What's Being Tested

### Endpoints (37 total)
- ✅ Authentication (3)
- ✅ Buyer Deals (4)
- ✅ Buyer Notifications (3)
- ✅ Buyer Preferences (2)
- ✅ Notification Preferences (8)
- ✅ Marketplace Accounts (7)
- ✅ Snap Studio (4)
- ✅ Pricing (5)

### Features
- ✅ User registration and JWT auth
- ✅ Role-based access control (buyer/seller/admin)
- ✅ Deal browsing and watch lists
- ✅ Notification management
- ✅ Marketplace account CRUD
- ✅ Snap studio job creation and publishing
- ✅ Market analysis and pricing data

### Error Handling
- ✅ 401 Unauthorized
- ✅ 403 Forbidden
- ✅ 404 Not Found
- ✅ 409 Conflict
- ✅ 422 Unprocessable Entity

---

## 🎯 Test Passes Available

### Pass A: Buyer Flow (5 min)
```
Register → Browse deals → Filter → Save deal → View saved → Manage preferences
```

### Pass B: Seller Snap (5 min)
```
Register → Create marketplace accounts → Create snap job → Publish to platforms
```

### Pass C: Marketplace Management (3 min)
```
Create account → List → Get → Update → Disconnect → Reconnect → Delete
```

### Pass D: Notification Preferences (3 min)
```
Get settings → Update frequency → Update score → Enable/disable → List options
```

### Pass E: Pricing & Analytics (3 min)
```
Get categories → Get stats → Get trends → Get your items → Create comparable
```

### Edge Cases (10 min)
```
Auth errors → RBAC violations → Not found → Conflicts → Validation → Boundaries
```

---

## 📊 Testing Methods Comparison

| Method | Setup | Speed | Visual | Shareable | Automated |
|--------|-------|-------|--------|-----------|-----------|
| **Swagger UI** | 0 min | Instant | ✅ | ❌ | ❌ |
| **Postman** | 2 min | Fast | ✅ | ✅ | ✅ |
| **VS Code REST** | 1 min | Instant | ❌ | ❌ | ❌ |
| **Python Script** | 0 min | 1 min | ❌ | ✅ | ✅ |
| **curl** | 0 min | Manual | ❌ | ✅ | ✅ |

---

## 🔧 Setup Checklist

- [ ] Backend running: `docker compose up -d`
- [ ] Backend healthy: Visit http://localhost:8000/docs
- [ ] Database ready: Check `docker compose logs api`
- [ ] Token generated: Run `python mint_jwt_tokens.py --buyer`
- [ ] Ready to test: Pick your method above

---

## 🎓 Learning Path

### New to Phase 4?
1. Start: `PHASE_4_COMPLETE.md` (2 min overview)
2. Understand: `PHASE_4_TESTING_KIT.md` (testing methods)
3. Follow: `PHASE_4_TEST_PASSES.md` (hands-on)
4. Reference: `PHASE_4_TESTING_GUIDE.md` (details)
5. Cheat Sheet: `TESTING_CHEAT_SHEET.md` (quick lookup)

### Experienced Developer?
1. Skim: `PHASE_4_COMPLETE.md` (status check)
2. Pick tool: REST Client or Postman
3. Run: `test_phase4_api.py` (quick validation)
4. Reference: `TESTING_CHEAT_SHEET.md` (specific endpoints)

### QA/Tester?
1. Read: `PHASE_4_TESTING_KIT.md` (overview)
2. Follow: `PHASE_4_TEST_PASSES.md` (procedures)
3. Use: `TESTING_CHEAT_SHEET.md` (edge cases)
4. Report: Any failures with endpoint and error

---

## 🚦 Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend Endpoints | ✅ Complete | All 37 endpoints working |
| Database Schema | ✅ Complete | All tables created |
| Authentication | ✅ Complete | JWT + RBAC working |
| Error Handling | ✅ Complete | All error codes handled |
| Documentation | ✅ Complete | 6 guides provided |
| Testing Tools | ✅ Complete | 5 methods available |
| Automation | ✅ Complete | Python + Postman ready |

---

## ⚡ Quick Commands

```bash
# Start backend
docker compose up -d

# Generate test tokens
python mint_jwt_tokens.py

# Run automated tests
python test_phase4_api.py

# Open Swagger UI
open http://localhost:8000/docs

# Check backend health
curl http://localhost:8000/docs
```

---

## 📞 Help & Support

### "Backend won't start"
```bash
docker compose up -d
docker compose logs api  # Check error logs
docker compose down && docker compose up -d  # Force restart
```

### "Getting 401 Unauthorized"
```bash
python mint_jwt_tokens.py --buyer  # Generate new token
# Copy token and use in requests
```

### "Getting 403 Forbidden"
```bash
# You're using wrong role for endpoint
# Use --seller flag if testing seller endpoints
python mint_jwt_tokens.py --seller
```

### "Need to understand an endpoint"
- See: `PHASE_4_TESTING_GUIDE.md` - Full endpoint reference
- Or: `TESTING_CHEAT_SHEET.md` - Quick reference
- Or: http://localhost:8000/docs - Interactive docs

### "Want to share with team"
- Export: `Deal-Scout-Phase4.postman_collection.json`
- Guide: `PHASE_4_TESTING_KIT.md`
- Reference: `PHASE_4_TESTING_GUIDE.md`

---

## ✅ Verification Checklist

Use this after testing to confirm everything works:

- [ ] User registration (auth/register)
- [ ] Can get JWT token
- [ ] Can authenticate with token
- [ ] Can browse deals (buyer/deals)
- [ ] Can save/unsave deals
- [ ] Can manage preferences
- [ ] Can create marketplace accounts
- [ ] Can create snap jobs
- [ ] Can view pricing data
- [ ] Auth errors return 401
- [ ] Permission errors return 403
- [ ] Not found errors return 404
- [ ] Duplicate errors return 409
- [ ] Validation errors return 422

---

## 📝 File Index

### Overview & Status
- **PHASE_4_COMPLETE.md** - Overall status and completion checklist
- **README_PHASE4_TESTING.md** - This file

### Testing Guides
- **PHASE_4_TESTING_KIT.md** - Master guide with all testing methods
- **TESTING_QUICK_START.md** - Quick start (3 ways to test)
- **PHASE_4_TESTING_GUIDE.md** - Detailed endpoint reference

### Practical Resources
- **PHASE_4_TEST_PASSES.md** - Step-by-step test procedures (5 passes + edge cases)
- **TESTING_CHEAT_SHEET.md** - Quick curl command reference

### Testing Tools
- **Deal-Scout-Phase4.postman_collection.json** - Postman collection (37 endpoints)
- **deal-scout-phase4.http** - VS Code REST Client file (46 requests)
- **mint_jwt_tokens.py** - JWT token generator
- **test_phase4_api.py** - Automated test script

---

## 🎉 Ready to Test?

### Fastest Path (5 minutes)
```bash
# 1. Start
docker compose up -d

# 2. Generate token
python mint_jwt_tokens.py --buyer

# 3. Test
python test_phase4_api.py
```

### Most Thorough Path (30 minutes)
1. Read: `PHASE_4_TESTING_KIT.md`
2. Follow: `PHASE_4_TEST_PASSES.md` (all 5 passes)
3. Test: Edge cases from same file
4. Verify: Checklist above

### Developer Path (10 minutes)
1. Use: VS Code REST Client (`deal-scout-phase4.http`)
2. Or: Postman (`Deal-Scout-Phase4.postman_collection.json`)
3. Or: Quick script (`python test_phase4_api.py`)

---

## 📞 Questions?

1. **How do I test?** → Read `PHASE_4_TESTING_KIT.md`
2. **What endpoints exist?** → See `PHASE_4_TESTING_GUIDE.md`
3. **Give me examples** → Use `TESTING_CHEAT_SHEET.md`
4. **Step by step?** → Follow `PHASE_4_TEST_PASSES.md`
5. **Generate token?** → Run `python mint_jwt_tokens.py`
6. **Run all tests?** → Execute `python test_phase4_api.py`
7. **Visual interface?** → Open http://localhost:8000/docs

---

**Phase 4 is ready for testing. Choose your method and start! 🚀**

Start with `PHASE_4_TESTING_KIT.md` for detailed guidance on each testing method.
