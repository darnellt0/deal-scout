# Deal Scout Ops Runbook

This runbook captures the minimal commands and checks needed to keep the local/staging stack healthy and to exercise the key buyer/seller flows that we verified.

## 1. Services

- Start everything with `docker compose up -d backend worker beat frontend postgres redis`.
- Health checks:
  - API: `curl http://localhost:8000/health`.
  - Worker: `docker compose logs worker --tail 20` (should show tasks registering, no tracebacks).

## 2. Tokens (demo)

All protected endpoints expect a JWT signed with `dev-secret-key-change-in-production`.

Examples (24h expiry):

```bash
# Buyer (user_id=1)
python -c "from datetime import datetime,timedelta;import jwt;print(jwt.encode({'user_id':1,'username':'testuser','email':'buyer@example.com','role':'buyer','exp':datetime.utcnow()+timedelta(hours=24),'iat':datetime.utcnow()},'dev-secret-key-change-in-production',algorithm='HS256'))"

# Seller (user_id=8)
python -c "from datetime import datetime,timedelta;import jwt;print(jwt.encode({'user_id':8,'username':'testuser_fresh','email':'seller8@example.com','role':'seller','exp':datetime.utcnow()+timedelta(hours=24),'iat':datetime.utcnow()},'dev-secret-key-change-in-production',algorithm='HS256'))"
```

Store the token in browser `localStorage.setItem('auth_token', '<token>')` or attach in `Authorization: Bearer <token>` headers for curl/HTTP clients.

## 3. Seller Snap Workflow

1. **Queue a job** (seller token):

```bash
PHOTO=$(base64 -w0 sample.jpg)  # or use provided single-pixel placeholder
curl -s -X POST http://localhost:8000/seller/snap \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photos\":[\"$PHOTO\"],\"notes\":\"CLI seed\",\"source\":\"api\"}"
```

2. **Worker processing:** confirm `docker compose logs worker --tail 20` shows `process_snap_job[...] succeeded`.

3. **Publish from API** (or through UI):

```bash
curl -s -X POST http://localhost:8000/seller/snap/<JOB_ID>/publish \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"snap_job_id":<JOB_ID>,"platforms":["ebay","facebook"],"price":180}'
```

4. **Verify DB (optional):**

```bash
docker compose exec postgres psql -U deals -d deals \
  -c "SELECT id,user_id,status FROM snap_jobs ORDER BY id DESC LIMIT 5;"
docker compose exec postgres psql -U deals -d deals \
  -c "SELECT id,my_item_id,platform,status FROM cross_posts ORDER BY id DESC LIMIT 5;"
```

## 4. Buyer Alerts & Notifications

Use the buyer token.

- **Create rule**

```bash
curl -s -X POST http://localhost:8000/deal-alert-rules \
  -H "Authorization: Bearer $BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop Deals","keywords":["laptop","gaming"],"max_price":1200,"notification_channels":["email"],"enabled":true}'
```

- **Test rule**: `curl -s -X POST http://localhost:8000/deal-alert-rules/<ID>/test -H "Authorization: Bearer $BUYER_TOKEN"`

- **Notification preferences**

```bash
# Channels
curl -s -X PATCH http://localhost:8000/notification-preferences/channels \
  -H "Authorization: Bearer $BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channels":["email","discord"]}'

# Quiet hours
curl -s -X PATCH http://localhost:8000/notification-preferences/quiet-hours \
  -H "Authorization: Bearer $BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quiet_hours_enabled":true,"quiet_hours_start":"21:30","quiet_hours_end":"07:15"}'

# Max per day
curl -s -X PATCH http://localhost:8000/notification-preferences/max-per-day \
  -H "Authorization: Bearer $BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_per_day":20}'

# Discord webhook
curl -s -X POST http://localhost:8000/notification-preferences/discord-webhook/add \
  -H "Authorization: Bearer $BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"discord_webhook_url":"https://example.com"}'
curl -s -X POST http://localhost:8000/notification-preferences/discord-webhook/test \
  -H "Authorization: Bearer $BUYER_TOKEN"
```

## 5. Health troubleshooting

- **Worker keeps reporting `like_new` errors:** confirm the latest `backend/app/buyer/search.py` is deployed; restart backend + worker.
- **Duplicate `deal_score` entries on manual scan:** 409 is expected when re-running blocking scan on the same snapshot; clear `listing_scores` if you need a fresh seed (`TRUNCATE listing_scores RESTART IDENTITY;`).
- **Publish endpoint errors:** ensure you’re using a seller-owned snap job (`snap_jobs.user_id` matches token) and provide at least one platform.

## 6. Browser UX checklist

- `/seller`: verify ready drafts appear with thumbnails, open publish form, publish successfully (status changes to “Published…”).
- `/buyer/alerts`: create & test alert rule, ensure modal shows sample matches.
- `/buyer/preferences`: toggle channels/quiet hours/max per day/Discord webhook without errors in console network tab.

## 7. Useful commands

- Tail backend logs: `docker compose logs backend -f`.
- Tail worker logs: `docker compose logs worker -f`.
- Reset database (danger!): `docker compose down -v` then `docker compose up`.

This document should be enough to validate builds, triage the most common issues, and demo the core buyer/seller journeys. Update as we add new workflows.
