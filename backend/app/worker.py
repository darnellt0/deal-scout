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
    # Multi-agent concurrent processing optimizations
    worker_prefetch_multiplier=4,  # Each worker prefetches 4 tasks for better throughput
    worker_max_tasks_per_child=100,  # Restart workers after 100 tasks to prevent memory leaks
    task_acks_late=True,  # Acknowledge tasks after completion for reliability
    task_reject_on_worker_lost=True,  # Re-queue tasks if worker dies
    worker_pool='prefork',  # Use prefork pool for CPU-bound tasks (vision processing)
    worker_concurrency=4,  # Default concurrency (can be overridden via CLI: --concurrency=N)
    task_compression='gzip',  # Compress task messages to reduce Redis memory
    result_compression='gzip',  # Compress results
    task_time_limit=300,  # Hard limit: 5 minutes per task
    task_soft_time_limit=240,  # Soft limit: 4 minutes (graceful timeout)
    beat_schedule={
        # SELLER-FOCUSED TASKS (MVP)
        "refresh-comps-nightly": {
            "task": "app.tasks.refresh_comps.refresh_comps_task",
            "schedule": crontab(hour=3, minute=0),
            "description": "Refresh pricing comps for seller price suggestions",
        },
        "reconcile-sales-hourly": {
            "task": "app.tasks.reconcile_sales.reconcile_sales_task",
            "schedule": crontab(minute=0),
            "description": "Sync marketplace sales and update inventory",
        },
        # BUYER TASKS (PARKED - restore if FEATURE_BUYER=true)
        # "scan-all-every-5-min": {
        #     "task": "app.tasks.scan_all.run_scan_all",
        #     "schedule": 300.0,
        #     "description": "Scan marketplaces for buyer deal discovery",
        # },
        # "send-digest-hourly": {
        #     "task": "app.tasks.notify.send_notifications",
        #     "schedule": crontab(minute=0),
        #     "description": "Send buyer deal notifications",
        # },
        # "check-deal-alerts-every-30-min": {
        #     "task": "check_all_deal_alerts",
        #     "schedule": 1800.0,
        #     "description": "Check buyer custom alert rules",
        # },
        # "check-price-drops-hourly": {
        #     "task": "check_price_drops",
        #     "schedule": 3600.0,
        #     "description": "Monitor buyer watchlist for price drops",
        # },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
