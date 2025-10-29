# First-Run Checklist Implementation for Deal Scout

## Overview

A complete "First-Run Checklist" banner system has been added to the deal-scout monorepo. This system provides initial setup guidance and verifies live features through a comprehensive backend API and health check system.

## Implementation Summary

### Files Created

1. **`backend/app/setup/__init__.py`**
   - Module initialization file for the setup package
   - Contains module docstring

2. **`backend/app/setup/router.py`** (Main implementation)
   - FastAPI router with prefix `/setup`
   - Three main endpoints + supporting health check functions
   - ~600 lines of well-documented code

3. **`backend/tests/test_setup.py`**
   - Comprehensive unit test suite
   - 40+ test cases covering all endpoints and checks
   - Tests for success/failure scenarios, mocking, and edge cases

### Files Modified

1. **`backend/app/main.py`**
   - Added import: `from app.setup.router import router as setup_router`
   - Added router registration: `app.include_router(setup_router, prefix="/setup", tags=["setup"])`

2. **`backend/app/tasks/__init__.py`**
   - Added simple `ping()` Celery task for worker health verification

## API Endpoints

### 1. GET `/setup/status`

**Purpose:** Returns a comprehensive JSON summary of all system setup checks.

**Response Structure:**
```json
{
  "ok": true,
  "checks": [
    {
      "id": "db",
      "label": "Database connected",
      "status": "ok|warn|fail",
      "details": "PostgreSQL/SQLite reachable"
    },
    ...
  ],
  "progress": 0.85,
  "timestamp": "2025-10-28T16:45:30.123456+00:00"
}
```

**Check IDs Performed:**
1. `db` - Database connectivity (SELECT 1)
2. `redis` - Redis PING test
3. `worker` - Celery worker running (ping task with 2s timeout)
4. `scheduler` - Celery Beat scheduler active (checks last scan timestamp)
5. `ebay` - eBay OAuth connected (queries marketplace_accounts table)
6. `craigslist` - Craigslist region configured (env var check)
7. `email` - Email delivery via SMTP (socket test to SMTP host)
8. `discord` - Discord webhook configured (env var check)
9. `sms` - SMS via Twilio configured (env vars + phone number check)
10. `demo` - Demo mode toggle status
11. `comps` - Local comps data loaded (furniture>sofas, furniture>kitchen_island)
12. `vision` - Vision pipeline enabled (env vars + module import test)
13. `static` - Sample images available (filesystem check)

**Status Values:**
- `ok` - Feature is configured and working
- `warn` - Feature is partially configured or needs attention
- `fail` - Feature has a critical error

**Progress Calculation:**
- `progress = count(ok checks) / total(checks)` → Float from 0.0 to 1.0

**Overall Status:**
- `ok = true` if both `db` and `redis` checks pass (critical dependencies)
- `ok = false` if any critical check fails

---

### 2. POST `/setup/test-notification`

**Purpose:** Send demo notifications through all enabled channels to verify delivery is working.

**Request:** No body required

**Response Structure:**
```json
{
  "success": true,
  "details": {
    "email": {
      "sent": true,
      "details": "Email sent via SMTP"
    },
    "discord": {
      "sent": false,
      "details": "Discord webhook not configured"
    },
    "sms": {
      "sent": false,
      "details": "Twilio credentials or target not configured"
    }
  },
  "timestamp": "2025-10-28T16:45:30.123456+00:00"
}
```

**Test Notifications Sent:**

1. **Email (via MailHog/SMTP)**
   - Subject: `[Deal Scout] Test Notification`
   - Includes branded HTML body with deal scout header
   - Sent to `settings.email_from` (default: alerts@local.test)

2. **Discord (via webhook)**
   - Message: "Deal Scout Test Notification"
   - Includes structured embed with title and color
   - Only sent if `DISCORD_WEBHOOK_URL` is configured

3. **SMS (via Twilio)**
   - Message: "Deal Scout setup verification: SMS delivery working!"
   - Sent to `settings.alert_sms_to`
   - Only sent if Twilio credentials + target number configured

**Success Criteria:**
- `success = true` if ANY channel successfully sent notification
- `success = false` if NO channels sent notifications

---

### 3. POST `/setup/dismiss`

**Purpose:** Record that user has dismissed the First-Run Checklist banner.

**Request:** No body required

**Response Structure:**
```json
{
  "dismissed": true,
  "timestamp": "2025-10-28T16:45:30.123456+00:00"
}
```

**Implementation Details:**
- Sets Redis key `setup:dismissed` with current timestamp
- No expiration (persists indefinitely)
- Single-user MVP (not user-specific)

---

### 4. GET `/setup/is-dismissed`

**Purpose:** Check if the First-Run Checklist has been dismissed.

**Response Structure:**
```json
{
  "dismissed": true,
  "dismissed_at": "2025-10-28T16:00:00.123456+00:00"
}
```

**Returns:**
- `dismissed = true` if flag exists in Redis
- `dismissed = false` if flag does not exist
- `dismissed_at = null` if never dismissed, or ISO timestamp if dismissed

---

## Health Check Implementation Details

### Database Check (`check_database`)
- Executes `SELECT 1` to verify connectivity
- Returns status and any error messages
- Status: `ok` if successful, `fail` if connection fails

### Redis Check (`check_redis`)
- Executes PING command
- Verifies Redis connection and availability
- Status: `ok` if successful, `fail` if connection fails

### Celery Worker Check (`check_celery_worker`)
- Enqueues a low-priority `ping` task
- Waits up to 2 seconds for worker response
- Non-blocking: returns `warn` if no response within timeout
- Status: `ok` if ping received, `warn` if timeout/unknown, `fail` if error

### Scheduler Check (`check_scheduler`)
- Checks Redis key `celery:beat:last_scan_ts` set by `scan_all` task
- Verifies scheduler activity within last 10 minutes
- Status: `ok` if recent activity, `warn` if stale or missing

### eBay Check (`check_ebay_connected`)
- Queries `marketplace_accounts` table
- Looks for: `platform='ebay' AND connected=true AND refresh_token present`
- Status: `ok` if connected account exists, `warn` otherwise

### Craigslist Check (`check_craigslist_configured`)
- Checks `CL_REGION` environment variable
- Returns region name in details (e.g., "sfbay")
- Status: `ok` if configured, `warn` otherwise

### Email Check (`check_email_configured`)
- Opens socket connection to SMTP host:port
- Timeout: 5 seconds
- Status: `ok` if reachable, `warn` if not

### Discord Check (`check_discord_configured`)
- Checks `DISCORD_WEBHOOK_URL` environment variable
- Status: `ok` if set, `warn` otherwise

### SMS Check (`check_sms_configured`)
- Checks for: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM`, `ALERT_SMS_TO`
- Status: `ok` if all present, `warn` if partially configured

### Demo Mode Check (`check_demo_mode`)
- Reads `DEMO_MODE` environment variable
- Returns "on" or "off" in details
- Status: always `ok` (informational)

### Comps Check (`check_comps_loaded`)
- Queries `comps` table for furniture categories
- Looks for: `category IN ('furniture>sofas', 'furniture>kitchen_island')`
- Status: `ok` if entries found, `warn` otherwise

### Vision Pipeline Check (`check_vision_pipeline`)
- Checks `VISION_ENABLED` and `REMBG_ENABLED` environment variables
- Attempts to import `app.vision.detector` module
- Status: `ok` if enabled and importable, `warn` otherwise

### Static Samples Check (`check_static_samples`)
- Checks filesystem for `backend/static/samples/` directory
- Counts files in directory
- Status: `ok` if directory exists with files, `warn` otherwise

---

## Integration with Existing Code

### Uses Existing Utilities
- `app.config.get_settings()` - Configuration management
- `app.core.db.get_session()` - Database connection
- `app.worker.celery_app` - Celery task enqueueing
- `app.notify.channels.send_email()` - Email sending
- `app.notify.channels.send_discord()` - Discord webhook
- `app.notify.channels.send_sms()` - SMS via Twilio

### Database Integration
- Queries existing tables: `marketplace_accounts`, `comps`
- No new tables created (simple KV via Redis for dismiss flag)

### Environment Variables Used
All read from `app.config.Settings`:
- Core: `DATABASE_URL`, `REDIS_URL`
- Features: `VISION_ENABLED`, `REMBG_ENABLED`, `DEMO_MODE`
- eBay: `EBAY_APP_ID` (connection status)
- Craigslist: `CL_REGION`
- Email: `SMTP_HOST`, `SMTP_PORT`, `EMAIL_FROM`
- Discord: `DISCORD_WEBHOOK_URL`
- SMS: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM`, `ALERT_SMS_TO`

---

## Testing

### Test File Location
`backend/tests/test_setup.py`

### Test Coverage
- **40+ unit tests** covering:
  - Response structure validation
  - Status value checks
  - Database query correctness
  - Environment variable reading
  - Mock-based testing for external services
  - Edge cases (no config, partial config, errors)

### Key Test Scenarios
1. GET `/setup/status` returns valid structure
2. All expected checks are present
3. Progress calculation is correct
4. POST `/setup/test-notification` with various channel configs
5. POST `/setup/dismiss` sets Redis flag
6. GET `/setup/is-dismissed` reads Redis flag
7. Individual check functions work correctly
8. Error handling in each check function

### Running Tests
```bash
cd backend
pytest tests/test_setup.py -v
```

---

## Caching Considerations

### Health Check Caching
The setup endpoint performs multiple database and network checks on each call. For production use, consider adding:
- Response caching with TTL (e.g., 30 seconds)
- Separate "quick" endpoint for frontend polls
- Background task to pre-compute status

### Example Implementation (if needed):
```python
from functools import lru_cache
from datetime import datetime, timedelta

_status_cache = {}
_cache_time = None

@router.get("/status")
async def get_setup_status():
    global _status_cache, _cache_time

    now = datetime.now()
    if _cache_time and (now - _cache_time) < timedelta(seconds=30):
        return _status_cache

    # Perform checks...
    _status_cache = result
    _cache_time = now
    return result
```

---

## Frontend Integration Guide

### Step 1: Fetch Status on App Load
```javascript
const response = await fetch('/setup/status');
const status = await response.json();
```

### Step 2: Display Banner if Not Dismissed
```javascript
const dismissedResponse = await fetch('/setup/is-dismissed');
const { dismissed } = await dismissedResponse.json();

if (!dismissed && !status.ok) {
  showFirstRunChecklistBanner(status.checks, status.progress);
}
```

### Step 3: Render Progress Bar
```javascript
const percentComplete = (status.progress * 100).toFixed(0);
// Render progress bar with percentComplete
```

### Step 4: Display Check Status
```javascript
status.checks.forEach(check => {
  const icon = check.status === 'ok' ? '✓' :
               check.status === 'warn' ? '⚠' : '✗';
  console.log(`${icon} ${check.label}: ${check.details}`);
});
```

### Step 5: Send Test Notification
```javascript
const testResponse = await fetch('/setup/test-notification', {
  method: 'POST'
});
const testResult = await testResponse.json();
// Display test notification results
```

### Step 6: Dismiss Banner
```javascript
const dismissResponse = await fetch('/setup/dismiss', {
  method: 'POST'
});
const { dismissed } = await dismissResponse.json();
// Hide banner
```

---

## Error Handling

### Network Errors
All endpoints gracefully handle:
- Database connection failures → `status: "fail"`
- Redis unavailability → `status: "fail"`
- Network timeouts → appropriate status returned
- Missing environment variables → `status: "warn"`

### Error Response Examples

**Database Connection Error:**
```json
{
  "id": "db",
  "label": "Database connected",
  "status": "fail",
  "details": "[Errno 111] Connection refused"
}
```

**Timeout Response:**
```json
{
  "id": "worker",
  "label": "Background worker running",
  "status": "warn",
  "details": "No response within 2s (may still be running)"
}
```

---

## Future Enhancements

### Possible Improvements
1. **Per-User Dismissal** - Store `setup:dismissed:{user_id}` in Redis
2. **Notification Rate Limiting** - Track last test notification per IP
3. **Custom Checks** - Plugin system for application-specific checks
4. **Status History** - Log check results over time for trend analysis
5. **Async Health Checks** - Run slow checks in background worker
6. **Webhooks** - Notify admin when critical checks fail
7. **Auto-Remediation** - Suggest or execute fixes for common issues

### Example: Rate Limiting Test Notifications
```python
@router.post("/test-notification")
async def test_notification(request: Request):
    client_ip = request.client.host
    last_test_key = f"setup:last_test:{client_ip}"

    if redis_client.exists(last_test_key):
        raise HTTPException(
            status_code=429,
            detail="Too many test notifications. Try again in 5 minutes."
        )

    # Send test notification...
    redis_client.setex(last_test_key, 300, "1")  # 5 minute cooldown

    return result
```

---

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `backend/app/setup/__init__.py` | 1 | Package init |
| `backend/app/setup/router.py` | 650+ | Main implementation |
| `backend/tests/test_setup.py` | 500+ | Unit tests |
| `backend/app/main.py` | Modified | Router registration |
| `backend/app/tasks/__init__.py` | Modified | Ping task |

**Total New Code:** ~1200 lines of Python

---

## Deployment Checklist

- [x] All files created and registered
- [x] Code compiles without errors
- [x] Unit tests written and passing
- [x] Error handling implemented
- [x] Documentation complete
- [ ] Frontend integration (next step)
- [ ] Load testing (if high volume expected)
- [ ] Production environment variables configured
- [ ] Database migrations (if any) applied

---

## Configuration Required

Ensure your `.env` file includes these for full functionality:

```bash
# Core (required)
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Features (optional, checks will mark as warn if missing)
VISION_ENABLED=true
REMBG_ENABLED=true
DEMO_MODE=false

# Craigslist (optional)
CL_REGION=sfbay

# Email (optional)
SMTP_HOST=mailhog
SMTP_PORT=1025
EMAIL_FROM=alerts@local.test

# Discord (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# SMS (optional)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM=+1234567890
ALERT_SMS_TO=+0987654321

# eBay (optional)
EBAY_APP_ID=...
```

---

## Support

For issues or questions about the First-Run Checklist implementation:
1. Check test file for usage examples
2. Review health check function source code in `backend/app/setup/router.py`
3. Verify environment variables are set
4. Check application logs for specific error messages

---

**Implementation Date:** October 28, 2025
**Status:** Complete and Ready for Frontend Integration
