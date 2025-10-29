# Deal Scout

Deal Scout is a two-sided marketplace assistant that continuously monitors popular marketplaces for high-value finds around San Jose, CA and streamlines cross-posting for sellers.

## Features
- **Buyer Radar**: Scan Craigslist, eBay, OfferUp, and Facebook Marketplace every 5 minutes for couches and kitchen islands, prioritizing free and great-value finds.
- **Deal Scoring**: Normalize marketplace data, compute a composite `deal_score`, and alert when free or high-scoring prospects surface.
- **Seller Snap Studio**: Accept photo uploads, run lightweight vision heuristics, clean/brighten images, draft copy, price with comps, and prepare cross-posts.
- **Celery Automation**: Scheduled tasks for scanning, refreshing comparables, reconciling sales, and dispatching notifications.
- **Full-Stack Monorepo**: FastAPI + Celery backend, Next.js + Tailwind frontend, Postgres + Redis infrastructure, all containerized via Docker Compose.

## Project Layout
```
deal-scout/
├─ docker-compose.yml
├─ .env.example
├─ README.md
├─ data/
│  └─ templates/default.txt
├─ backend/
│  ├─ Dockerfile
│  ├─ pyproject.toml
│  ├─ app/
│  │  ├─ adapters/… (marketplace fetchers)
│  │  ├─ buyer/… (search, templates, API)
│  │  ├─ seller/… (snap pipeline, pricing)
│  │  ├─ vision/… (detection + cleanup)
│  │  ├─ core/… (models, db, scoring)
│  │  └─ tasks/… (Celery tasks & router)
│  └─ tests/
└─ frontend/
   ├─ Dockerfile
   ├─ package.json
   ├─ app/… (Next.js App Router views)
   └─ components/, lib/, public/
```

## Getting Started
1. **Copy environment settings**
   ```bash
   cp .env.example .env
   ```
   Fill in API credentials (OpenAI, eBay, etc.) if available.

2. **Launch the stack**
   ```bash
   docker compose up --build
   ```
   Services:
   - `backend`: FastAPI on `http://localhost:8000`
   - `worker`: Celery worker
   - `beat`: Celery beat scheduler
   - `frontend`: Next.js on `http://localhost:3000`
   - `postgres`: Primary database
   - `redis`: Broker/result backend

3. **Explore**
   - Buyer feed: `http://localhost:3000/buyer`
   - Seller Snap Studio: `http://localhost:3000/seller`
   - API docs (FastAPI Swagger): `http://localhost:8000/docs`

## Celery Schedule
- `scan_all` – every 5 minutes (marketplace sweep).
- `refresh_comps` – nightly at 3 AM Pacific (comparable sales refresh).
- `reconcile_sales` – hourly (cross-post reconciliation).
- `notify` task is available on-demand to flush pending alerts.

## Key API Endpoints
- `GET /health` – service heartbeat check.
- `POST /tasks/scan` – queue a marketplace scan.
- `GET /buyer/deals` – retrieve scored deals (used by the frontend).
- `POST /seller/snap` – create a new image-first listing draft.
- `GET /seller/snap/{job_id}` – check Snap job status/progress.
- `POST /seller/pricing/suggest` – price suggestion from comps.

## Development Notes
- Backend dependencies are defined in `backend/pyproject.toml`.
- Frontend uses Next.js App Router with Tailwind; `npm run dev` for local development.
- Tests: a sample FastAPI health check lives in `backend/tests/test_health.py`.
- Default templates for buyer outreach live under `data/templates/`.

### Local Demo with Fixtures (No APIs)
1. Start services:
   ```bash
   docker compose up -d
   ```
2. Apply migrations (once):
   ```bash
   make migrate
   ```
3. Seed data (fixtures + images + comps):
   ```bash
   python scripts/seed_mock_data.py
   ```
4. Optional: preload Snap-to-Sell items:
   ```bash
   python scripts/seed_snap_items.py
   ```
5. Optional: create demo notifications:
   ```bash
   python scripts/demo_alerts.py
   ```
6. Open:
   - Buyer dashboard: http://localhost:3000/
   - Snap-to-Sell: http://localhost:3000/seller
   - MailHog (emails): http://localhost:8025
7. Cleanup:
   ```bash
   python scripts/wipe_dev_db.py
   # or
   python scripts/wipe_dev_db.py --force
   ```

**Notes**
- All fixtures are within 50 miles of San Jose except one outlier to illustrate radius filtering.
- Pricing suggestions use local `data/fixtures/sold_comps.*.json` when API tokens are absent or `PRICE_SUGGESTION_MODE` is not `ebay_only`.
- Sample images are generated on demand in `backend/static/samples/`, keeping the repository lightweight.

#### Quick Test Commands
- **Seed everything**
  ```bash
  python scripts/seed_mock_data.py && python scripts/seed_snap_items.py && python scripts/demo_alerts.py
  ```
- **List a few top deals (couch, <=$150, within 50mi)**
  ```bash
  curl "http://localhost:8000/listings?category=couch&price_max=150&radius_mi=50" | jq '.[:3]'
  ```
- **Trigger manual scan (fixtures already loaded)**
  ```bash
  curl -X POST http://localhost:8000/scan/run
  ```
- **Check prepared Snap-to-Sell jobs**
  ```bash
  curl http://localhost:8000/seller/snap | jq
  ```

## Next Steps & Enhancements
1. Replace adapter fallbacks with live integrations (Craigslist RSS parsing, eBay Finding API auth, OfferUp/Facebook automation).
2. Expand the vision pipeline with real image labeling and condition estimation (potentially via OpenAI Vision or custom models).
3. Implement outbound notification channels (email/SMS) and marketplace cross-post publishing (eBay API + guided posting flows).

## Connecting eBay (Sandbox)
1. Ensure the stack is running.
2. Retrieve the authorization URL:
   `ash
   curl http://localhost:8000/ebay/authorize
   `
3. Open the URL in a browser, complete login, and copy the returned code.
4. Exchange the code for a refresh token:
   `ash
   curl -X POST http://localhost:8000/ebay/exchange \
     -H "Content-Type: application/json" \
     -d '{"code":"<PASTE_CODE>"}'
   `
5. Confirm the connection by checking marketplace_accounts (connected=true).

## Enabling Notifications
- Email is wired to MailHog by default at http://localhost:8025.
- Discord: set DISCORD_WEBHOOK_URL in .env to post to a channel.
- SMS (optional): set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, and ALERT_SMS_TO.

## Demo Mode Toggle
- The header toggle switches between fixture-backed scans and live marketplace sweeps.
- When Demo Mode is on, /scan/run defaults to fixtures. Disable to force live=1.

## Craigslist Regions
- Configure CL_REGION in .env (e.g., sfbay, sacramento).
- CL_SEARCH_FURN controls the Craigslist category code (default sss).
- Enable CL_ENABLE_FREE to include the free-stuff RSS feed alongside category searches.

## Reliable Startup (Auto-Restart + Migrations)

The backend now uses a resilient entrypoint that:
- **Waits for Postgres** to be healthy (up to 60 seconds with feedback)
- **Auto-retries Alembic migrations** with exponential backoff (2s, 4s, 8s, 16s, 32s, 64s)
- **Handles DB unavailability gracefully** — the service starts even if migrations fail, but subsequent queries will fail until DB is repaired
- **Auto-restarts on failure** — Docker Compose uses `restart: unless-stopped` to recover from crashes

To manually bounce the backend (e.g., after DB reset):
```powershell
powershell -ExecutionPolicy Bypass -File scripts/win/restart-backend.ps1
```

This will:
1. Restart the backend container
2. Re-run the entrypoint (DB wait + migrations)
3. Show the last 50 log lines
4. Report health status when ready

**Key Log Markers:**
- `[entrypoint] Waiting for Postgres...` — Connectivity check in progress
- `[entrypoint] ✓ DB connectivity check complete.` — DB is reachable
- `[entrypoint] Running database migrations...` — Alembic starting
- `[entrypoint] ✓ Migrations applied successfully.` — Schema is ready
- `[entrypoint] Starting Uvicorn application...` — App launching

## Quick Windows Health Checks

If you're running on Windows + Docker Desktop, use these shortcuts to verify the stack:

### Start the Stack
```bash
docker compose up -d
```

### Verify Health
```bash
python scripts/dev_doctor.py
```
This checks:
- Backend is listening on port 8000
- `/health` and `/ping` endpoints respond correctly
- Database (Postgres) and Redis are reachable
- Reports status as JSON for scripting

### Tail Logs with Filters
```powershell
powershell -ExecutionPolicy Bypass -File scripts/win/logs.ps1 -Service backend -Match "health|scan|error"
```
Available services: `backend`, `worker`, `beat`, `postgres`, `redis`

### Run a Live Scan
```powershell
powershell -ExecutionPolicy Bypass -File scripts/win/scan.ps1 -Live -Blocking
```
- **-Live**: Use live marketplaces (default) vs. fixtures
- **-Blocking**: Wait for results (default) vs. queue asynchronously

Example: Queue a fixture-based scan without blocking
```powershell
scripts/win/scan.ps1 -Live:$false -Blocking:$false
```

### Troubleshooting

**"Backend port 8000 not listening"**
```bash
docker compose logs backend
```
Check for startup errors in the logs.

**"Health check reports DB or Redis down"**
```bash
docker compose logs postgres
docker compose logs redis
```

**"Scan endpoint not responding"**
```bash
# Is the worker running?
docker compose logs worker

# Try a direct HTTP check
curl http://localhost:8000/ping
```

**"Logs show import errors"**
Rebuild the container:
```bash
docker compose build --no-cache backend
docker compose up -d
```
