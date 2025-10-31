# Database Debugging Report

**Date:** 2025-10-29
**Status:** Root causes identified and documented
**Priority:** Critical - Must fix before Phase 4 testing can complete

---

## Executive Summary

Found **5 critical database/model schema mismatches** causing 500 errors:

1. ✅ **MyItem model missing `user_id` field** - FOUND
2. ✅ **MarketplaceAccount model missing `user_id` field** - FOUND
3. ✅ **UserPref model type mismatch** - FOUND
4. ⚠️ **Buyer deals endpoints missing** - FOUND
5. ⚠️ **Notification preferences initialization** - FOUND

---

## Error #1: MyItem.user_id Missing (CRITICAL)

### Location
- **Model File:** `backend/app/core/models.py` (Lines 147-160)
- **Route File:** `backend/app/routes/my_items.py` (Line 35)
- **Pricing File:** `backend/app/seller/pricing.py` (Line 193)

### Problem
```python
# backend/app/core/models.py - Lines 147-160
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
    # ❌ MISSING: user_id field!
```

### Code Trying to Use It
```python
# backend/app/seller/pricing.py - Line 193
items = (
    db.query(MyItem)
    .filter(MyItem.user_id == current_user.id)  # ❌ AttributeError!
    .order_by(MyItem.created_at.desc())
    .all()
)
```

### Error Message
```
AttributeError: type object 'MyItem' has no attribute 'user_id'
```

### Fix Required
Add to `MyItem` model in `backend/app/core/models.py` (line 150):
```python
user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
```

**Full corrected model:**
```python
class MyItem(Base):
    __tablename__ = "my_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # ← ADD THIS
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

---

## Error #2: MarketplaceAccount Missing `user_id` (CRITICAL)

### Location
- **Model File:** `backend/app/core/models.py` (Lines 163-170)
- **Route File:** `backend/app/routes/marketplace_accounts.py`

### Problem
```python
# backend/app/core/models.py - Lines 163-170
class MarketplaceAccount(Base):
    __tablename__ = "marketplace_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(50))
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
    credentials: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # ❌ MISSING: user_id field!
    # ❌ MISSING: account_username field!
    # ❌ MISSING: is_active field!
```

### Code Trying to Use It
Routes in `marketplace_accounts.py` create and filter by user but model has no `user_id`.

### Fix Required
Add fields to `MarketplaceAccount`:
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

---

## Error #3: UserPref Model Type Mismatch (MODERATE)

### Location
- **Model File:** `backend/app/core/models.py` (Lines 118-132)

### Problem
```python
# backend/app/core/models.py - Line 122
class UserPref(Base):
    __tablename__ = "user_prefs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True)  # ❌ Should be int, not str!
```

### Issue
- `user_id` is defined as `String(64)` but should be `Integer`
- Foreign key to `users.id` (which is Integer)
- Will cause type mismatch in queries

### Fix Required
```python
user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)  # ← Change to int
```

---

## Error #4: Buyer Deals Endpoints Not Found

### Location
- **Route:** `GET /buyer/deals`
- **Expected File:** `backend/app/buyer/routes.py`

### Problem
The OpenAPI schema shows no `/buyer/deals` endpoints, but code exists to create them.

### Evidence
From testing:
```
GET /buyer/deals → 404 Not Found
GET /buyer/deals/saved → 404 Not Found
POST /buyer/deals/1/save → 404 Not Found
```

### Likely Cause
Routes not registered in main router. Check `backend/app/main.py` for:
```python
app.include_router(buyer.router)  # May be missing
```

---

## Error #5: Notification Preferences Not Initialized (MODERATE)

### Location
- **Endpoint:** `GET /notification-preferences`
- **Table:** `notification_preferences` (doesn't exist)

### Problem
- New users don't have preferences created
- Endpoint tries to query non-existent table
- No migration creates this table

### Fix Required
1. **Create table:** Add migration for `notification_preferences`
2. **Auto-initialize:** Add trigger or post-registration logic to create default preferences for new users

---

## Affected Endpoints

### 🔴 Critical (500 Errors - Fix Required)

| Endpoint | Error | Cause | Line |
|----------|-------|-------|------|
| `GET /my-items` | AttributeError | MyItem.user_id missing | models.py:150 |
| `GET /seller/pricing/my-items` | AttributeError | MyItem.user_id missing | pricing.py:193 |
| `POST /marketplace-accounts` | Database error | MarketplaceAccount.user_id missing | models.py:166 |
| `GET /marketplace-accounts` | Database error | MarketplaceAccount.user_id missing | models.py:166 |
| `POST /seller/snap` | Unknown | Need to investigate | Unknown |
| `GET /notification-preferences` | Database error | Table doesn't exist | Unknown |

### 🟡 Warning (404 Errors - Routes Missing)

| Endpoint | Error | Cause |
|----------|-------|-------|
| `GET /buyer/deals` | 404 Not Found | Routes not registered? |
| `GET /buyer/deals/saved` | 404 Not Found | Routes not registered? |
| `POST /buyer/deals/1/save` | 404 Not Found | Routes not registered? |

---

## Fix Checklist

- [ ] **Step 1:** Add `user_id` field to `MyItem` model (line 150)
- [ ] **Step 2:** Add `user_id`, `account_username`, `is_active` to `MarketplaceAccount` (line 164)
- [ ] **Step 3:** Fix `user_id` type in `UserPref` from `str` to `int` (line 122)
- [ ] **Step 4:** Run database migrations: `python -m alembic upgrade head`
- [ ] **Step 5:** Verify buyer routes registered in `app/main.py`
- [ ] **Step 6:** Create notification_preferences migration
- [ ] **Step 7:** Re-test all endpoints

---

## Implementation Priority

### Priority 1 (Do First)
1. Add `user_id` to MyItem
2. Add user fields to MarketplaceAccount
3. Run migrations

### Priority 2 (Then)
4. Fix UserPref type
5. Check buyer routes registration
6. Re-test endpoints

### Priority 3 (Later)
7. Initialize notification preferences
8. Add remaining missing features

---

## Testing After Fixes

```bash
# After making changes:
1. cd backend
2. python -m alembic upgrade head  # Run migrations
3. docker compose restart backend  # Restart API
4. pytest tests/ -v  # Run tests
5. Test endpoints in REST Client
```

---

## Files to Modify

1. **`backend/app/core/models.py`**
   - Line 150: Add `user_id` to MyItem
   - Line 164: Add `user_id`, `account_username`, `is_active` to MarketplaceAccount
   - Line 122: Fix `user_id` type in UserPref

2. **`backend/alembic/versions/`**
   - Create new migration with schema changes

3. **`backend/app/main.py`**
   - Verify buyer routes are registered

---

## Database Schema After Fixes

### my_items table (current → fixed)
```sql
-- Current (broken)
CREATE TABLE my_items (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    category VARCHAR(120),
    attributes JSONB,
    condition VARCHAR(50),
    price FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Fixed
CREATE TABLE my_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),  ← ADD
    title VARCHAR(255),
    category VARCHAR(120),
    attributes JSONB,
    condition VARCHAR(50),
    price FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### marketplace_accounts table (current → fixed)
```sql
-- Current (broken)
CREATE TABLE marketplace_accounts (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50),
    connected BOOLEAN,
    credentials JSONB,
    created_at TIMESTAMP
);

-- Fixed
CREATE TABLE marketplace_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),  ← ADD
    platform VARCHAR(50),
    account_username VARCHAR(255),  ← ADD
    is_active BOOLEAN DEFAULT TRUE,  ← ADD
    connected BOOLEAN,
    credentials JSONB,
    created_at TIMESTAMP
);
```

---

## Next Steps

1. **Apply fixes to models.py**
2. **Create and run migration**
3. **Restart backend container**
4. **Re-test endpoints**
5. **Update FINAL_TESTING_REPORT.md** with results

---

**Report Generated:** 2025-10-29
**Status:** Ready for implementation
**Severity:** 🔴 CRITICAL - Blocks most seller features

