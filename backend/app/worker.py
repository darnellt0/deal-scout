from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "deal_scout",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    timezone=settings.app_timezone,
    beat_schedule={
        "scan-all-every-5-min": {
            "task": "app.tasks.scan_all.run_scan_all",
            "schedule": 300.0,
        },
        "refresh-comps-nightly": {
            "task": "app.tasks.refresh_comps.refresh_comps_task",
            "schedule": crontab(hour=3, minute=0),
        },
        "reconcile-sales-hourly": {
            "task": "app.tasks.reconcile_sales.reconcile_sales_task",
            "schedule": crontab(minute=0),
        },
        "send-digest-hourly": {
            "task": "app.tasks.notify.send_notifications",
            "schedule": crontab(minute=0),
        },
        # Phase 7: Deal Alerts
        "check-deal-alerts-every-30-min": {
            "task": "check_all_deal_alerts",
            "schedule": 1800.0,  # 30 minutes
        },
        "check-price-drops-hourly": {
            "task": "check_price_drops",
            "schedule": 3600.0,  # 1 hour
        },
        # Phase 7: Digest Emails
        "send-daily-digests": {
            "task": "send_daily_digests",
            "schedule": crontab(hour=9, minute=0),  # 9 AM daily
        },
        "send-weekly-digests": {
            "task": "send_weekly_digests",
            "schedule": crontab(day_of_week=1, hour=9, minute=0),  # Monday 9 AM
        },
        "cleanup-old-notifications-weekly": {
            "task": "cleanup_old_notifications",
            "schedule": crontab(day_of_week=0, hour=2, minute=0),  # Sunday 2 AM
        },
        # Phase 7: Price Analysis
        "update-all-price-analyses-daily": {
            "task": "update_all_price_analyses",
            "schedule": crontab(hour=3, minute=30),  # 3:30 AM daily
        },
        "analyze-new-listings-hourly": {
            "task": "analyze_new_listings",
            "schedule": crontab(minute=30),  # Every hour at :30
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
