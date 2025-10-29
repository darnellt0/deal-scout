# Windows + Docker Health Check & Live Scan Patch

This patch hardens the `deal-scout` stack for reliable health checks and live scans on Windows + Docker Desktop.

## Changes Summary

### A) Backend: Guaranteed /health + Safe Startup

**File: `backend/app/main.py`**
- ✓ Added `/ping` endpoint for quick connectivity checks (responds instantly)
- ✓ Added `_wait_for_db()` function with exponential backoff retry logic (max 30s)
- ✓ Moved DB retry to lifespan startup, preventing server crashes on DB race conditions
- ✓ Ensures health endpoint responds OK even if DB is temporarily unavailable

### B) Docker Configuration: Real Healthchecks + Service Dependencies

**File: `docker-compose.yml`**
- ✓ Removed deprecated `version: "3.9"` key (Docker Compose v2+ auto-detects)
- ✓ Updated backend healthcheck from Python urllib to `wget` (more reliable cross-platform)
- ✓ Backend healthcheck: 10s interval, 3s timeout, 30 retries (100s total tolerance)
- ✓ Updated Postgres healthcheck: 5s interval, 3s timeout, 20 retries
- ✓ Updated Redis healthcheck: 5s interval, 3s timeout, 20 retries
- ✓ Added proper service dependencies with `condition: service_healthy`
  - Worker + Beat wait for Postgres + Redis healthy
  - Frontend waits for Backend healthy
- ✓ Added `--proxy-headers --forwarded-allow-ips="*"` to Uvicorn command (fixes reverse proxy detection)

**File: `backend/Dockerfile`**
- ✓ Added `wget` to base image (for healthcheck probe)
- ✓ Added `netcat-openbsd` for `wait-for-db.sh` compatibility
- ✓ Copied and made executable `wait-for-db.sh` script

**File: `backend/wait-for-db.sh`** (New)
- Simple shell script that waits for Postgres to be ready via netcat
- Used optionally before Uvicorn startup on Windows environments
- Returns when port is listening (not dependent on full DB init)

### C) Diagnostics: Cross-Platform "Doctor" Script

**File: `scripts/dev_doctor.py`** (New)
- Python tool to verify entire stack from Windows/macOS/Linux
- Checks:
  1. Backend port 8000 listening
  2. GET /health endpoint (checks DB + Redis status internally)
  3. GET /ping endpoint (quick connectivity test)
  4. Postgres port 5432 listening
  5. Redis port 6379 listening
- Outputs human-readable + machine-parseable JSON
- No external dependencies beyond `requests` (already in backend requirements)

### D) Windows PowerShell Helpers

**File: `scripts/win/logs.ps1`** (New)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/win/logs.ps1 -Service backend -Match "scan|error"
```
- Streams Docker Compose logs with case-insensitive filtering
- Available services: backend, worker, beat, postgres, redis

**File: `scripts/win/scan.ps1`** (New)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/win/scan.ps1 -Live -Blocking
```
- Triggers scan via POST /scan/run
- Modes:
  - `-Live`: Use real marketplaces (default)
  - `-Blocking`: Wait for results synchronously (default)
- Example: Queue fixture-based scan: `scan.ps1 -Live:$false -Blocking:$false`

### E) Documentation: README Windows Section

**File: `README.md`** (Updated)
- Added "Quick Windows Health Checks" section
- Includes start, verify, logs, scan, and troubleshooting subsections
- Cross-references all new tools with examples

## Acceptance Criteria ✓

All criteria from the patch specification are met:

1. **docker compose up -d** → Backend health becomes healthy
2. **curl http://localhost:8000/health** → Returns JSON immediately (no empty reply)
3. **python scripts/dev_doctor.py** → Prints ok: true on healthy stack
4. **scripts/win/scan.ps1 -Live -Blocking** → Returns live scan counts
5. **scripts/win/logs.ps1 -Service backend -Match error** → Streams logs with Select-String filters
6. **Backend startup is race-condition-safe** → Retries DB connection with exponential backoff

## Quick Start

```bash
# 1. Start stack
docker compose up -d

# 2. Verify health
python scripts/dev_doctor.py

# 3. Run a blocking scan (fixtures)
powershell -ExecutionPolicy Bypass -File scripts/win/scan.ps1 -Live:$false -Blocking

# 4. Tail logs with filters
powershell -ExecutionPolicy Bypass -File scripts/win/logs.ps1 -Service backend -Match scan
```

## Key Improvements for Windows

1. **Health endpoint always responds** — Even if DB is starting, /health returns 200
2. **Proper service ordering** — No race conditions with compose startup
3. **Reliable healthchecks** — Uses wget instead of Python subprocess (more stable on Windows)
4. **PowerShell-native tooling** — Win-friendly scan & log helpers
5. **Diagnostics tool** — Single command to verify entire stack
6. **DB retry loop** — Exponential backoff prevents port-not-ready crashes

## Files Modified/Created

```
✓ backend/app/main.py              (enhanced health + ping + DB retry)
✓ backend/Dockerfile               (added wget + netcat + wait-for-db.sh)
✓ backend/wait-for-db.sh           (new: DB readiness check)
✓ docker-compose.yml               (healthchecks + dependencies)
✓ scripts/dev_doctor.py            (new: diagnostics)
✓ scripts/win/logs.ps1             (new: PowerShell logs helper)
✓ scripts/win/scan.ps1             (new: PowerShell scan helper)
✓ README.md                        (new Windows section)
```

## Testing

To validate the patch, run:

```bash
# Full stack healthcheck
python scripts/dev_doctor.py

# Should report: ok: true, all services healthy

# Tail errors only
powershell -ExecutionPolicy Bypass -File scripts/win/logs.ps1 -Service backend -Match "ERROR|exception"

# Run blocking scan
powershell -ExecutionPolicy Bypass -File scripts/win/scan.ps1 -Live:$false -Blocking
# Should return counts: total, new, updated, skipped
```

## Notes for Production

- The health endpoint intentionally returns 200 even if DB is unavailable (Docker/Kubernetes can still start containers)
- If you need stricter health checks, modify `/health` to return 503 on DB failure (but be aware this can deadlock service startup)
- The `wait-for-db.sh` is optional—can be removed if you prefer pure retry logic in the application
- Tested on Windows + Docker Desktop with Python 3.11+
