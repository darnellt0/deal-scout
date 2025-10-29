from __future__ import annotations

from celery import shared_task

from app.core.db import get_session
from app.core.models import CrossPost, Order


@shared_task(name="app.tasks.reconcile_sales.reconcile_sales_task")
def reconcile_sales_task():
    reconciled = 0
    with get_session() as session:
        posts = (
            session.query(CrossPost)
            .filter(CrossPost.status == "pending")
            .order_by(CrossPost.created_at.asc())
            .limit(10)
            .all()
        )
        for post in posts:
            order = Order(
                cross_post_id=post.id,
                platform_order_id=f"{post.platform}-{post.id}",
                status="closed",
                total=0.0,
                metadata={"note": "Synthetic reconciliation"},
            )
            session.add(order)
            post.status = "closed"
            reconciled += 1
    return {"reconciled": reconciled}
