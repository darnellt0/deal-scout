# Deal Scout Deployment Guide

This guide covers deploying Deal Scout to production using **Render** (backend/worker/database) and **Vercel** (frontend).

## Architecture Overview

```
┌─────────────┐
│   Vercel    │  ← Next.js Frontend
│  (Frontend) │
└──────┬──────┘
       │ API calls
       ↓
┌─────────────┐     ┌──────────────┐
│   Render    │────→│   Render     │
│  (Backend)  │     │  (Worker)    │
│  FastAPI    │     │  Celery      │
└──────┬──────┘     └───────┬──────┘
       │                    │
       └────────┬───────────┘
                ↓
       ┌────────────────┐
       │  Render Postgres │
       │  Render Redis   │
       └────────────────┘
```

## Prerequisites

- GitHub repository with your code
- [Render](https://render.com) account
- [Vercel](https://vercel.com) account
- AWS S3 bucket (for image hosting)
- Marketplace API credentials (eBay, Facebook, OfferUp)

## Part 1: Render Setup (Backend Infrastructure)

### 1. Create PostgreSQL Database

1. Go to Render Dashboard → "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `deal-scout-db`
   - **Database**: `deals`
   - **User**: `deals`
   - **Region**: Oregon (or closest to you)
   - **Plan**: Free (or Starter for production)
3. Click "Create Database"
4. **Save the Internal Database URL** (starts with `postgresql://`)

### 2. Create Redis Instance

1. Go to "New +" → "Redis"
2. Configure:
   - **Name**: `deal-scout-redis`
   - **Region**: Same as database
   - **Plan**: Free (or Starter)
   - **Maxmemory Policy**: `allkeys-lru`
3. Click "Create Redis"
4. **Save the Internal Redis URL** (starts with `redis://`)

### 3. Deploy Backend (FastAPI)

1. Go to "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `deal-scout-api`
   - **Region**: Same as database/redis
   - **Branch**: `main` (or your production branch)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3.11`
   - **Build Command**:
     ```bash
     pip install -e .
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free (or Starter for production)

4. **Environment Variables** (click "Add Environment Variable"):

   ```bash
   # Database & Redis (use Internal URLs from steps 1-2)
   DATABASE_URL=<postgres-internal-url>
   REDIS_URL=<redis-internal-url>

   # Feature Flags
   FEATURE_BUYER=false
   FEATURE_BG_CLEAN=false
   FEATURE_ADV_VISION=false
   FEATURE_LIVE_PRICING=false

   # AI Services (required)
   ANTHROPIC_API_KEY=<your-claude-api-key>
   # OR
   OPENAI_API_KEY=<your-openai-api-key>

   # Image Storage (S3 - required for production)
   AWS_REGION=us-west-2
   AWS_ACCESS_KEY_ID=<your-aws-key>
   AWS_SECRET_ACCESS_KEY=<your-aws-secret>
   S3_BUCKET=<your-bucket-name>
   S3_IMAGE_PREFIX=images/

   # eBay (Production credentials)
   EBAY_ENV=production
   EBAY_APP_ID=<your-ebay-app-id>
   EBAY_CERT_ID=<your-ebay-cert-id>
   EBAY_DEV_ID=<your-ebay-dev-id>
   EBAY_REDIRECT_URI=https://deal-scout-api.onrender.com/ebay/callback
   EBAY_SCOPE=https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory

   # Facebook Marketplace
   FACEBOOK_APP_ID=<your-facebook-app-id>
   FACEBOOK_APP_SECRET=<your-facebook-app-secret>

   # OfferUp
   OFFERUP_CLIENT_ID=<your-offerup-client-id>
   OFFERUP_CLIENT_SECRET=<your-offerup-client-secret>

   # Backend URL (update after deployment)
   BACKEND_URL=https://deal-scout-api.onrender.com

   # CORS (update after frontend deployment)
   CORS_ORIGINS=https://deal-scout.vercel.app

   # Application Settings
   APP_TIMEZONE=America/Los_Angeles
   DEFAULT_CITY=San Jose, CA
   DEFAULT_RADIUS_MI=50
   DEMO_MODE=false
   LOG_LEVEL=INFO

   # Email (optional - use real SMTP in production)
   EMAIL_FROM=noreply@dealscout.app
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=<your-sendgrid-api-key>
   SMTP_USE_TLS=true

   # Monitoring (optional)
   SENTRY_DSN=<your-sentry-dsn>
   ```

5. Click "Create Web Service"
6. Wait for deployment (5-10 minutes)
7. **Save the URL**: `https://deal-scout-api.onrender.com`

### 4. Deploy Celery Worker

1. Go to "New +" → "Background Worker"
2. Connect same repository
3. Configure:
   - **Name**: `deal-scout-worker`
   - **Region**: Same as backend
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3.11`
   - **Build Command**:
     ```bash
     pip install -e .
     ```
   - **Start Command**:
     ```bash
     celery -A app.worker worker --loglevel=info
     ```
   - **Plan**: Free (or Starter)

4. **Environment Variables**: Use the same variables as backend (copy from backend service)

5. Click "Create Background Worker"

### 5. Deploy Celery Beat (Scheduler)

1. Go to "New +" → "Background Worker"
2. Configure:
   - **Name**: `deal-scout-beat`
   - **Region**: Same as backend
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3.11`
   - **Build Command**:
     ```bash
     pip install -e .
     ```
   - **Start Command**:
     ```bash
     celery -A app.worker beat --loglevel=info
     ```
   - **Plan**: Free

3. **Environment Variables**: Copy from backend
4. Click "Create Background Worker"

## Part 2: Vercel Setup (Frontend)

### 1. Deploy Frontend

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (or leave default)
   - **Output Directory**: `.next` (or leave default)

5. **Environment Variables**:

   ```bash
   # Backend API URL (use your Render backend URL)
   NEXT_PUBLIC_API_BASE_URL=https://deal-scout-api.onrender.com
   ```

6. Click "Deploy"
7. Wait for deployment (2-5 minutes)
8. **Save the URL**: `https://deal-scout.vercel.app` (or your custom domain)

### 2. Update Backend CORS

1. Go back to Render → Backend Service → Environment
2. Update `CORS_ORIGINS`:
   ```bash
   CORS_ORIGINS=https://deal-scout.vercel.app,https://deal-scout-preview.vercel.app
   ```
3. Save and redeploy

## Part 3: Post-Deployment Configuration

### 1. Run Database Migrations

Render automatically runs migrations via `entrypoint.sh`, but you can manually trigger:

```bash
# SSH into Render backend service (use Render shell)
python -m alembic upgrade head
```

### 2. Create Admin User (Optional)

```bash
# In Render shell
python scripts/create_admin_user.py --email admin@dealscout.app
```

### 3. Test OAuth Flows

#### eBay OAuth
1. Visit: `https://deal-scout-api.onrender.com/ebay/authorize`
2. Complete eBay login
3. Copy the authorization code
4. Exchange for token:
   ```bash
   curl -X POST https://deal-scout-api.onrender.com/ebay/exchange \
     -H "Content-Type: application/json" \
     -d '{"code":"<paste-code-here>"}'
   ```

#### Facebook OAuth
1. Visit: `https://deal-scout-api.onrender.com/facebook-oauth/authorize`
2. Complete Facebook login
3. Token automatically stored

#### OfferUp OAuth
1. Visit: `https://deal-scout-api.onrender.com/offerup-oauth/authorize`
2. Complete OfferUp login
3. Token automatically stored

### 4. Verify Health

```bash
# Check backend health
curl https://deal-scout-api.onrender.com/health

# Should return:
# {"ok": true, "db": true, "redis": true, "queue_depth": 0, ...}
```

### 5. Test Image Upload

1. Go to `https://deal-scout.vercel.app`
2. Click "Start Selling"
3. Upload a test photo
4. Verify it appears in S3 bucket
5. Check backend logs in Render for processing

## Part 4: Custom Domain (Optional)

### Frontend Domain (Vercel)

1. Go to Vercel project → Settings → Domains
2. Add your domain (e.g., `www.dealscout.app`)
3. Update DNS records as instructed
4. Wait for SSL certificate (automatic)

### Backend Domain (Render)

1. Go to Render backend service → Settings → Custom Domain
2. Add your API subdomain (e.g., `api.dealscout.app`)
3. Update DNS with CNAME record
4. Wait for SSL (automatic)

**Update environment variables:**
- Backend: `BACKEND_URL=https://api.dealscout.app`
- Frontend: `NEXT_PUBLIC_API_BASE_URL=https://api.dealscout.app`
- Backend CORS: `CORS_ORIGINS=https://www.dealscout.app`

## Part 5: Monitoring & Maintenance

### 1. Set Up Sentry (Errors)

1. Create Sentry project at https://sentry.io
2. Get DSN
3. Add to Render backend environment:
   ```bash
   SENTRY_DSN=<your-sentry-dsn>
   ```
4. Redeploy

### 2. Monitor Logs

**Render Logs:**
- Backend: Render Dashboard → deal-scout-api → Logs
- Worker: Render Dashboard → deal-scout-worker → Logs
- Beat: Render Dashboard → deal-scout-beat → Logs

**Vercel Logs:**
- Vercel Dashboard → Project → Deployments → View Logs

### 3. Database Backups

Render Starter plan includes daily backups. To manually backup:

1. Render Dashboard → deal-scout-db → Backups
2. Click "Create Backup"

### 4. Scale Up (When Ready)

**Render:**
- Database: Upgrade to Starter ($7/mo) for better performance
- Backend: Upgrade to Starter ($7/mo) for more CPU/RAM
- Worker: Upgrade if processing lag occurs

**Vercel:**
- Free tier is generous for MVP
- Upgrade to Pro ($20/mo) for analytics and better limits

## Part 6: Troubleshooting

### Backend won't start
- Check Render logs for import errors
- Verify `DATABASE_URL` and `REDIS_URL` are Internal URLs (not External)
- Ensure all required env vars are set

### Worker not processing jobs
- Check worker logs
- Verify `REDIS_URL` matches backend
- Confirm Beat scheduler is running

### Images not uploading
- Check S3 bucket permissions (public ACL allowed)
- Verify AWS credentials
- Check backend logs for upload errors

### CORS errors
- Verify `CORS_ORIGINS` includes exact frontend URL
- Check for trailing slashes
- Redeploy backend after CORS changes

### OAuth not working
- Verify callback URLs in marketplace developer portals
- Check credentials (App ID, Secret, etc.)
- Ensure HTTPS is used (not HTTP)

## Production Checklist

- [ ] Postgres database created and migrated
- [ ] Redis instance running
- [ ] Backend deployed and healthy (`/health` returns OK)
- [ ] Worker deployed and processing
- [ ] Beat scheduler running
- [ ] Frontend deployed and accessible
- [ ] CORS configured correctly
- [ ] S3 bucket configured with public ACL
- [ ] Environment variables set (no secrets in code!)
- [ ] OAuth flows tested for all marketplaces
- [ ] Sentry monitoring configured
- [ ] SSL certificates active (both frontend and backend)
- [ ] Custom domains configured (if applicable)
- [ ] Test end-to-end: Upload photo → Generate listing → Publish → Verify on marketplace

## Costs Estimate

**Free Tier (MVP):**
- Render Postgres: Free (512 MB, 90 days)
- Render Redis: Free (25 MB)
- Render Backend: Free (512 MB RAM, sleeps after 15 min inactivity)
- Render Worker: Free
- Render Beat: Free
- Vercel: Free (hobby)
- **Total**: $0/month

**Starter (Production):**
- Render Postgres Starter: $7/mo
- Render Redis Starter: $10/mo
- Render Backend Starter: $7/mo
- Render Worker Starter: $7/mo
- Render Beat Starter: $7/mo
- Vercel Pro: $20/mo
- AWS S3: ~$1-5/mo (depending on traffic)
- **Total**: ~$59-63/month

## Support

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Issues**: GitHub Issues on your repository

---

**🎉 Deployment Complete!** Visit your frontend URL and start cross-posting!
