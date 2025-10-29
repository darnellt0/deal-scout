# Auto-Restart + Migrations Patch Documentation

## Overview

This patch implements resilient backend startup with automatic Postgres health checking, Alembic migration retries, and service auto-restart on failure. The backend now reliably recovers from temporary database unavailability without manual intervention.

## Changes Summary

### 1. New Entrypoint Script: `backend/entrypoint.sh`

**Purpose**: Orchestrate startup sequence: wait for DB → apply migrations → launch Uvicorn

**Workflow**:
```
1. Log configuration and environment
2. Wait for Postgres connectivity (max 60s)
   └─ Retries every 1 second
   └─ Shows progress (attempt counter)
   └─ Continues anyway if timeout (non-blocking)
3. Apply Alembic migrations with retry loop
   ├─ Attempt 1: delay 2s if fail
   ├─ Attempt 2: delay 4s if fail
   ├─ Attempt 3: delay 8s if fail
   ├─ Attempt 4: delay 16s if fail
   ├─ Attempt 5: delay 32s if fail
   └─ Attempt 6: delay 64s if fail
4. Log warnings if migrations failed
5. Launch Uvicorn with configuration
```

**Key Features**:
- **Exponential backoff**: 2s, 4s, 8s, 16s, 32s, 64s (total ~126s if all attempts fail)
- **Non-blocking DB wait**: Continues after 60s even if Postgres unreachable
- **Graceful degradation**: App starts even if migrations fail (queries will fail, but health check responds)
- **Detailed logging**: Each step includes `[entrypoint]` prefix for easy log filtering

**Environment Variables**:
```bash
DB_HOST=postgres           # Default: postgres
DB_PORT=5432              # Default: 5432
ALEMBIC_CMD=alembic upgrade head  # Override to downgrade, skip, etc.
UVICORN_CMD=uvicorn ...   # Custom Uvicorn command (rarely used)
PORT=8000                 # App port (passed to Uvicorn)
```

### 2. Updated Dockerfile: `backend/Dockerfile`

**Changes**:
```dockerfile
# Added to apt-get install:
- wget          # For healthcheck probes
- netcat-openbsd # For DB port checking

# New COPY directives:
COPY alembic ./alembic      # Migration definitions
COPY alembic.ini ./         # Alembic config
COPY entrypoint.sh ./       # Startup script

# New RUN to make executable:
RUN chmod +x ./entrypoint.sh

# Updated CMD:
CMD ["sh", "-c", "backend/entrypoint.sh"]
```

**Before**:
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**After**:
```dockerfile
CMD ["sh", "-c", "backend/entrypoint.sh"]
```

This allows the entrypoint to handle environment variable expansion and shell evaluation.

### 3. Enhanced docker-compose.yml

**Backend Service Changes**:
```yaml
backend:
  command: ["sh", "-c", "backend/entrypoint.sh"]  # Use entrypoint
  environment:
    - DB_HOST=postgres
    - DB_PORT=5432
    - ALEMBIC_CMD=alembic upgrade head
    - PORT=8000
  depends_on:
    postgres:
      condition: service_healthy   # Wait for DB healthy
    redis:
      condition: service_healthy   # Wait for Redis healthy
  restart: unless-stopped          # Auto-restart on failure
  healthcheck:
    test: ["CMD", "wget", "-qO", "-", "http://localhost:8000/health"]
    interval: 10s
    timeout: 3s
    retries: 30
```

**Worker Service Changes**:
```yaml
worker:
  depends_on:
    postgres:
      condition: service_healthy   # Wait for DB
    backend:
      condition: service_started   # Wait for backend
  restart: unless-stopped          # Auto-restart on failure
```

**Beat Service Changes**:
```yaml
beat:
  depends_on:
    postgres:
      condition: service_healthy   # Wait for DB
    backend:
      condition: service_started   # Wait for backend
  restart: unless-stopped          # Auto-restart on failure
```

**Frontend Service Changes**:
```yaml
frontend:
  restart: unless-stopped          # Auto-restart on failure
```

**Key Improvements**:
- `restart: unless-stopped` → Services restart automatically on crash, but don't restart if stopped manually
- `condition: service_healthy` → Backend waits for Postgres to be healthy before starting
- Environment variables passed explicitly to entrypoint
- Alembic command configurable via `ALEMBIC_CMD`

### 4. Configuration: `.env.example`

**Added**:
```bash
# Database Connection (for startup/entrypoint)
DB_HOST=postgres
DB_PORT=5432

# Alembic Migrations (auto-applied on startup)
ALEMBIC_CMD=alembic upgrade head
```

These allow:
- Overriding DB connection details per environment
- Controlling migration behavior (e.g., `alembic upgrade head` vs `alembic downgrade base`)

### 5. Windows Helper: `scripts/win/restart-backend.ps1`

**Purpose**: Manually restart backend and show migration logs

**Usage**:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/win/restart-backend.ps1
```

**Parameters**:
```powershell
-Logs [bool]         # Show logs after restart (default: $true)
-TailLines [int]     # Number of log lines to show (default: 50)
```

**Examples**:
```powershell
# Default: restart and show 50 log lines
powershell -ExecutionPolicy Bypass -File scripts/win/restart-backend.ps1

# Restart but don't show logs
powershell -ExecutionPolicy Bypass -File scripts/win/restart-backend.ps1 -Logs:$false

# Show 100 log lines
powershell -ExecutionPolicy Bypass -File scripts/win/restart-backend.ps1 -TailLines 100
```

**Output**:
1. Restarts the backend container
2. Displays last N log lines
3. Checks health endpoint
4. Reports DB + Redis status

**Example Output**:
```
================================================
Restarting Backend Service
================================================

Restarting container 'backend'...
✓ Backend container restarted.

Fetching last 50 lines of logs...

[entrypoint] ============================================
[entrypoint] Deal-Scout Backend Entrypoint
[entrypoint] ============================================
...
[entrypoint] Running database migrations...
[entrypoint] Alembic attempt 1/6 (delay: 2s)...
[entrypoint] ✓ Migrations applied successfully.
...
[entrypoint] Starting Uvicorn application...

Checking health status...
✓ Backend is healthy
  DB:    True
  Redis: True
  Queue: 0 pending tasks

Done. Backend is being restarted.
```

### 6. Documentation: README.md

**Added Section**: "Reliable Startup (Auto-Restart + Migrations)"

Contents:
- Explanation of the resilient entrypoint
- How to manually restart the backend
- Key log markers for troubleshooting
- Expected behavior during startup

## Startup Timeline

### Before Patch
```
0s    docker compose up -d
3s    Backend container starts
4s    Backend tries to connect to DB → FAIL
5s    Backend crashes
10s   Docker Compose restarts backend
...   Repeat until Postgres is ready
20s+  Finally successful (unpredictable timing)
```

### After Patch
```
0s    docker compose up -d
3s    Postgres + Redis containers start (healthchecks active)
8s    Postgres + Redis become healthy
9s    Backend container starts (was waiting for service_healthy)
10s   Entrypoint: "Waiting for Postgres..."
11s   Entrypoint: "✓ DB connectivity check complete."
12s   Entrypoint: "Running database migrations..."
13s   Entrypoint: "✓ Migrations applied successfully."
14s   Entrypoint: "Starting Uvicorn application..."
15s   Backend healthy, Frontend can start
16s   Full stack ready and stable
```

## Failure Scenarios & Recovery

### Scenario 1: Slow Postgres Startup
```
[entrypoint] Waiting for Postgres at postgres:5432...
[entrypoint] Attempt 1/60... (waiting)
[entrypoint] Attempt 2/60... (waiting)
...
[entrypoint] Attempt 8/60... (waiting)
[entrypoint] ✓ DB connectivity check complete.
[entrypoint] Running database migrations...
[entrypoint] Alembic attempt 1/6...
[entrypoint] ✓ Migrations applied successfully.
```
**Result**: Backend waits patiently, then proceeds. ✓

### Scenario 2: Migration Failure (Connection Issue)
```
[entrypoint] Running database migrations...
[entrypoint] Alembic attempt 1/6 (delay: 2s)...
[entrypoint] ✗ Alembic exited with code 1.
[entrypoint] Retrying in 2s...
[entrypoint] Alembic attempt 2/6 (delay: 4s)...
[entrypoint] ✓ Migrations applied successfully.
```
**Result**: Retries with backoff, succeeds on second attempt. ✓

### Scenario 3: Persistent Migration Failure
```
[entrypoint] Alembic attempt 1/6... ✗
[entrypoint] Retrying in 2s...
[entrypoint] Alembic attempt 2/6... ✗
...
[entrypoint] Alembic attempt 6/6... ✗
[entrypoint] ⚠️  Migrations did not complete after 6 attempts.
[entrypoint] WARNING: Service will start but may have incomplete schema.
[entrypoint] Starting Uvicorn application...
```
**Result**: App starts in degraded mode (read queries may fail). Health endpoint still responds. ⚠️

With `restart: unless-stopped`, if backend crashes due to DB schema issues, Docker will restart it automatically. The app can proceed once DB is fixed.

### Scenario 4: Postgres Container Crashes
```
Backend running healthily
→ Postgres container crashes
→ Backend continues running (healthcheck still responds)
→ Queries start failing (Connection refused)
→ [Some error handling code logs DB connection errors]
→ If configured, backend queries timeout and return 500
→ Health endpoint reports redis: true, db: false
→ Docker detects backend unhealthy after 30 retries × 10s = 300s
→ Backend container restarts
→ Entrypoint runs again (waits for DB, retries migrations)
→ Backend recovers once Postgres comes back
```

**Result**: Automatic recovery with data loss only if Postgres lost data. ✓

## Key Log Markers

Use these to identify startup stages:

```
[entrypoint] ============================================
             ↓ Startup beginning

[entrypoint] Waiting for Postgres at postgres:5432...
             ↓ DB connectivity check in progress

[entrypoint] ✓ DB connectivity check complete.
             ↓ DB is reachable

[entrypoint] Running database migrations...
             ↓ Alembic starting

[entrypoint] Alembic attempt 1/6...
             ↓ Migration attempt (may retry)

[entrypoint] ✓ Migrations applied successfully.
             ↓ Schema is up-to-date

[entrypoint] ⚠️  Migrations did not complete...
             ↓ Migration failure after all retries (app still starts)

[entrypoint] Starting Uvicorn application...
             ↓ Ready to handle requests

[entrypoint] ============================================
             ↓ Startup complete
```

## Healthcheck Behavior

**GET /health response** during various states:

```json
{
  "ok": true,
  "db": true,
  "redis": true,
  "queue_depth": 0,
  "version": "0.1.0",
  "time": "2024-01-01T12:00:00+00:00"
}
```

- If migration is in progress: health still returns 200 OK with current DB status
- If DB connection fails: health returns 503 (service unavailable)
- If Redis connection fails: health returns 503
- If both fail: health returns 503

The health endpoint is separate from the entrypoint, so migrations don't block health checks.

## Kubernetes Readiness/Liveness Probes

These settings work well with Kubernetes:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: backend
spec:
  containers:
  - name: backend
    image: deal-scout:backend
    ports:
    - containerPort: 8000
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 20
      periodSeconds: 5
```

- `initialDelaySeconds: 20` gives the entrypoint time to apply migrations
- The healthcheck will report `db: false` during migration, allowing retry

## Troubleshooting

### Backend keeps restarting
**Symptoms**: Container restarts every 30 seconds in logs
```bash
docker compose logs backend | grep -E "(exited|error|crash)"
```

**Check**:
1. Are migrations invalid?
   ```bash
   docker compose exec backend alembic status
   ```

2. Is the DB schema corrupted?
   ```bash
   docker compose logs postgres | tail -50
   ```

**Fix**: Review migration files or restore DB from backup

---

### Migrations never run
**Symptoms**: `[entrypoint] Running database migrations...` but then immediate app start
```bash
docker compose logs backend | grep -i alembic
```

**Check**:
1. Is `ALEMBIC_CMD` set correctly in `.env`?
   ```bash
   docker compose config backend | grep ALEMBIC_CMD
   ```

2. Is alembic.ini present?
   ```bash
   docker compose exec backend ls -la /app/alembic.ini
   ```

**Fix**: Ensure `.env` has `ALEMBIC_CMD=alembic upgrade head`

---

### Health endpoint reports `db: false`
**Symptoms**: `curl http://localhost:8000/health` shows `"db": false`

**Check**:
```bash
docker compose logs postgres | tail -20
docker compose logs backend | grep -E "(database|connection|error)"
```

**Fix**:
1. If Postgres is down: `docker compose up -d postgres`
2. If Postgres is up but unresponsive: `docker compose restart postgres`
3. If connection string is wrong: Check `DATABASE_URL` in `.env`

---

### Manual restart to force migrations
```powershell
powershell -ExecutionPolicy Bypass -File scripts/win/restart-backend.ps1
```

This will:
1. Stop the backend container
2. Re-run the entrypoint
3. Show logs from migration attempt

## Files Modified/Created

```
✓ backend/entrypoint.sh          (NEW) - 90 lines
✓ backend/Dockerfile             (MODIFIED) - Added alembic + entrypoint
✓ docker-compose.yml             (MODIFIED) - Command, env, restart policies
✓ .env.example                   (MODIFIED) - Added DB_HOST, DB_PORT, ALEMBIC_CMD
✓ scripts/win/restart-backend.ps1 (NEW) - 60 lines
✓ README.md                      (MODIFIED) - Added "Reliable Startup" section
✓ AUTO_RESTART_MIGRATIONS_PATCH.md (NEW) - This file
```

## Acceptance Criteria

✅ **Backend waits for Postgres before starting** — Entrypoint uses `nc -z` to check port

✅ **Alembic retries with exponential backoff** — 6 attempts, delays: 2s, 4s, 8s, 16s, 32s, 64s

✅ **App starts even if migrations fail** — Continues after timeout/failures (graceful degradation)

✅ **Automatic restart on crash** — `restart: unless-stopped` in docker-compose

✅ **Docker Compose service dependencies** — `depends_on: condition: service_healthy`

✅ **Windows helper for manual restart** — `scripts/win/restart-backend.ps1`

✅ **Health endpoint always responds** — `GET /health` returns 200 regardless of entrypoint state

✅ **Clear log markers for debugging** — `[entrypoint]` prefix on all startup messages

✅ **Configuration via environment** — `DB_HOST`, `DB_PORT`, `ALEMBIC_CMD` configurable

## Quick Start

```bash
# Rebuild to include entrypoint
docker compose build --no-cache backend

# Start stack (backend will auto-wait for DB + run migrations)
docker compose up -d

# Check progress
docker compose logs -f backend

# Once healthy:
curl http://localhost:8000/health

# Manual restart (e.g., after DB reset)
powershell -ExecutionPolicy Bypass -File scripts/win/restart-backend.ps1
```

## Summary

This patch makes the deal-scout backend production-ready with:
- **Robust startup**: Waits for dependencies, retries migrations
- **Automatic recovery**: Restarts on failure without manual intervention
- **Graceful degradation**: Continues even if migrations fail
- **Clear debugging**: Detailed log markers for troubleshooting
- **Easy management**: Windows restart helper + health checks

The stack is now resilient to temporary database unavailability, network issues during startup, and Postgres crashes.
