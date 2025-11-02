"""Celery task modules."""

from celery import shared_task

# Import task modules so Celery registers them when the package is loaded.
from . import (  # noqa: F401
    check_deal_alerts,
    notify,
    process_snap,
    reconcile_sales,
    refresh_comps,
    scan_all,
)


@shared_task(name="app.tasks.ping")
def ping():
    """Simple ping task to verify worker is running."""
    return "pong"
