# Archived Features

This directory contains code that has been parked during the seller-first MVP refactor.

## What's Here

All buyer-focused features have been moved here to simplify the codebase while keeping them available for future restoration.

## Archived Components

### Backend (`backend-buyer-features/`)
- **Adapters** (`app/adapters/`) - Marketplace scrapers for buyer deal discovery
  - `ebay_api.py` - eBay Finding API for deal scanning
  - `facebook_marketplace.py` - Facebook Marketplace scraper
  - `offerup.py` - OfferUp listing fetcher
  - `craigslist_rss.py` - Craigslist RSS feed parser

- **Buyer Routes** (`app/buyer/`) - All buyer-specific API endpoints
  - Deal feed endpoints
  - Alert management
  - Notification preferences
  - Watchlist functionality

- **Buyer Tasks** (`app/tasks/`) - Celery tasks for buyer features
  - `scan_all.py` - Marketplace scanning task (runs every 5 min)
  - `check_deal_alerts.py` - Deal alert monitoring
  - `notify.py` - Buyer notification dispatcher

- **Buyer Models** - Database models (keep in DB but unused)
  - `Listing` - Scraped marketplace listings
  - `ListingScore` - Deal scoring results
  - `DealAlertRule` - Custom buyer alerts
  - `WatchlistItem` - Price tracking

### Frontend (`frontend-buyer-features/`)
- **Pages** (`app/buyer/`) - All buyer UI pages
  - Deal feed page
  - Alert management page
  - Preferences page

- **Components**
  - `AlertCard.tsx` - Deal display component
  - `CreateAlertModal.tsx` - Alert creation UI
  - `AlertRuleCard.tsx` - Alert rule display

## Why Was This Parked?

The initial Deal Scout product served both buyers (finding deals) and sellers (cross-posting). For MVP clarity and focus, we're prioritizing the seller cross-posting workflow, which has:

1. Clear value proposition: One photo → multiple marketplace listings
2. Fewer dependencies: No need for marketplace scraping
3. Better unit economics: Sellers pay for convenience vs. free buyer alerts
4. Simpler maintenance: OAuth APIs vs. brittle scrapers

Buyer features remain valuable but represent a separate product direction.

## How to Restore

### Quick Restoration (If Needed)

1. **Enable Feature Flag:**
   ```bash
   # In .env
   FEATURE_BUYER=true
   ```

2. **Restore Backend Code:**
   ```bash
   # Copy adapters back
   cp -r archive/backend-buyer-features/app/adapters/* backend/app/adapters/

   # Copy buyer routes back
   cp -r archive/backend-buyer-features/app/buyer/* backend/app/buyer/

   # Copy buyer tasks back
   cp -r archive/backend-buyer-features/app/tasks/* backend/app/tasks/
   ```

3. **Restore Frontend Code:**
   ```bash
   # Copy buyer pages back
   cp -r archive/frontend-buyer-features/app/buyer/* frontend/app/buyer/

   # Copy buyer components back
   cp -r archive/frontend-buyer-features/components/* frontend/components/
   ```

4. **Restore Routes in main.py:**
   - Uncomment buyer route registrations in `backend/app/main.py`

5. **Restore Celery Tasks:**
   - Uncomment buyer task registrations in `backend/app/worker.py`
   - Uncomment buyer beat schedule in `backend/app/worker.py`

### Full Reactivation Checklist

- [ ] Enable `FEATURE_BUYER=true` in environment
- [ ] Restore buyer backend code from archive
- [ ] Restore buyer frontend code from archive
- [ ] Restore buyer routes in FastAPI app
- [ ] Restore buyer tasks in Celery worker
- [ ] Re-enable buyer beat schedules
- [ ] Update frontend navigation to show buyer links
- [ ] Run database migrations (if buyer models were modified)
- [ ] Test marketplace scrapers (may need API key updates)
- [ ] Test deal alert pipeline end-to-end
- [ ] Update documentation to reflect dual-mode operation

## Dependencies to Check

If restoring buyer features, verify these external dependencies:

- **eBay Finding API**: Ensure `EBAY_APP_ID` is valid
- **Craigslist RSS**: Verify `CL_REGION` and `CL_SEARCH_FURN` settings
- **Facebook/OfferUp Scrapers**: May need to update selectors/endpoints
- **Notification Services**:
  - MailHog (dev) or SMTP (prod) for email
  - Discord webhook URL for Discord alerts
  - Twilio credentials for SMS

## Archive Date

**2025-11-08** - Seller-first MVP refactor (Phase 1)

## Notes

- Database tables for buyer features (`listings`, `listing_scores`, `deal_alert_rules`, etc.) are kept intact but unused
- The `Comp` model is **NOT** archived as it's shared with seller pricing logic
- Buyer API routes are removed but models remain for potential future use
- All code in this archive was functional at time of archival
