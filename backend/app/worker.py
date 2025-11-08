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
            "task": "app.tasks.check_deal_alerts.check_all_deal_alerts",
            "schedule": 1800.0,  # 30 minutes
        },
        "check-price-drops-hourly": {
            "task": "app.tasks.check_deal_alerts.check_price_drops",
            "schedule": 3600.0,  # 1 hour
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
