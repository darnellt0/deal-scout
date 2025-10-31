# Quick Fix Guide - Database Schema Issues

## Summary
Found and documented 5 critical database schema mismatches. This guide shows exactly what to fix.

---

## Fix #1: Add user_id to MyItem Model

**File:** `backend/app/core/models.py`
**Lines:** 147-160

### Current Code (BROKEN)
```python
class MyItem(Base):
    __tablename__ = "my_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(120))
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    condition: Mapped[Optional[Condition]] = mapped_column(Enum(Condition))
    price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

### Fixed Code
```python
class MyItem(Base):
    __tablename__ = "my_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # ← ADD THIS LINE
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(120))
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    condition: Mapped[Optional[Condition]] = mapped_column(Enum(Condition))
    price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

**What Changed:** Added one line after `id` field
```python
user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
```

---

## Fix #2: Add user_id, account_username, is_active to MarketplaceAccount

**File:** `backend/app/core/models.py`
**Lines:** 163-170

### Current Code (BROKEN)
```python
class MarketplaceAccount(Base):
    __tablename__ = "marketplace_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(50))
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
    credentials: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Fixed Code
```python
class MarketplaceAccount(Base):
    __tablename__ = "marketplace_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # ← ADD
    platform: Mapped[str] = mapped_column(String(50))
    account_username: Mapped[str] = mapped_column(String(255))  # ← ADD
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # ← ADD
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
    credentials: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**What Changed:** Added three lines after `id` field
```python
user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
platform: Mapped[str] = mapped_column(String(50))
account_username: Mapped[str] = mapped_column(String(255))
is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

---

## Fix #3: Fix UserPref user_id Type

**File:** `backend/app/core/models.py`
**Line:** 122

### Current Code (BROKEN)
```python
class UserPref(Base):
    __tablename__ = "user_prefs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True)  # ❌ Wrong type!
```

### Fixed Code
```python
class UserPref(Base):
    __tablename__ = "user_prefs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)  # ✅ Fixed!
```

**What Changed:**
- Type: `Mapped[str]` → `Mapped[int]`
- Column: `String(64)` → `ForeignKey("users.id")`

---

## Steps to Apply Fixes

### Step 1: Edit models.py
1. Open `backend/app/core/models.py`
2. Make the three changes above
3. Save the file

### Step 2: Create Database Migration
```bash
cd backend
python -m alembic revision --autogenerate -m "Add user_id and account fields to models"
```

### Step 3: Run Migration
```bash
python -m alembic upgrade head
```

### Step 4: Restart Backend
```bash
docker compose restart backend
```

### Step 5: Verify Fixes
```bash
# Test /my-items endpoint (should work now)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/my-items

# Test /marketplace-accounts endpoint (should work now)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/marketplace-accounts
```

---

## Expected Results After Fixes

### Before Fixes
```
GET /my-items
Response: 500 Internal Server Error
{
  "error": "INTERNAL_ERROR",
  "message": "An internal error occurred"
}
```

### After Fixes
```
GET /my-items
Response: 200 OK
{
  "meta": {"page": 1, "size": 20, "total": 6},
  "items": [
    {"id": 1, "title": "iPhone 12 Pro", ...},
    {"id": 2, "title": "AirPods Pro", ...},
    ...
  ]
}
```

---

## Verification Checklist

- [ ] Edited MyItem class (added user_id field)
- [ ] Edited MarketplaceAccount class (added user_id, account_username, is_active)
- [ ] Edited UserPref class (changed user_id type from str to int)
- [ ] Created migration with `alembic revision --autogenerate`
- [ ] Ran migration with `alembic upgrade head`
- [ ] Restarted backend with `docker compose restart backend`
- [ ] Tested `/my-items` endpoint
- [ ] Tested `/marketplace-accounts` endpoint
- [ ] All endpoints return 200 OK (not 500 errors)

---

## Troubleshooting

### Migration Fails
```
Error: Column "user_id" does not exist on table "my_items"
```
**Solution:** The table exists but the column doesn't. Alembic should create it. Try:
```bash
python -m alembic upgrade head --sql  # See what SQL will run
```

### Backend Won't Start
```
Error: sqlalchemy.exc.ProgrammingError: column "user_id" does not exist
```
**Solution:** Migration didn't run. Check:
```bash
python -m alembic current  # See current version
python -m alembic history  # See all migrations
python -m alembic upgrade head  # Run pending migrations
```

### Endpoint Still Returns 500
1. Check backend logs: `docker logs deal-scout-backend-1 | tail -50`
2. Look for new error messages
3. Verify all three model changes were applied
4. Verify migration ran successfully

---

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `backend/app/core/models.py` | Add user_id to MyItem | +1 line |
| `backend/app/core/models.py` | Add fields to MarketplaceAccount | +3 lines |
| `backend/app/core/models.py` | Fix UserPref user_id type | 1 line |
| `backend/alembic/versions/*` | Auto-generated migration | (created) |

---

## Time Estimate

- **Edit files:** 5 minutes
- **Create migration:** 2 minutes
- **Run migration:** 1 minute
- **Restart backend:** 30 seconds
- **Test endpoints:** 2 minutes

**Total:** ~11 minutes

---

## Success Indicators

✅ Models edited correctly
✅ Migration created without errors
✅ Migration ran without errors
✅ Backend started without errors
✅ `/my-items` returns 200 OK
✅ `/marketplace-accounts` returns 200 OK

Once you see these checkmarks, the database schema issues are fixed!

