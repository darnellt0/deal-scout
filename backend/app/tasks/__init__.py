"""Celery task modules."""

from celery import shared_task


@shared_task(name="app.tasks.ping")
def ping():
    """Simple ping task to verify worker is running."""
    return "pong"
