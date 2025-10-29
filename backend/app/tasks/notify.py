from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from celery import shared_task

from app.core.db import get_session
from app.core.models import Notification
from app.notify.channels import send_email


def _render_digest(groups: Dict[str, List[Notification]]) -> str:
    sections = []
    for category, items in groups.items():
        rows = []
        for notification in items:
            payload = notification.payload
            rows.append(
                f"<li><a href='{payload['url']}'>{payload['title']}</a> · "
                f"${float(payload.get('price', 0)):.0f} · score {payload['deal_score']} · "
                f"{payload.get('distance_mi', '?')} mi</li>"
            )
        sections.append(
            f"<h3>{category.title()}</h3><ul>{''.join(rows)}</ul>"
        )
    body = "<h2>Deal Scout Digest</h2>" + "".join(sections)
    return body


@shared_task(name="app.tasks.notify.send_notifications")
def send_notifications():
    sent = 0
    with get_session() as session:
        notifications = (
            session.query(Notification)
            .filter(Notification.status == "pending", Notification.channel == "digest")
            .order_by(Notification.created_at.asc())
            .limit(50)
            .all()
        )
        if not notifications:
            return {"sent": 0}

        grouped: Dict[str, List[Notification]] = defaultdict(list)
        for notification in notifications:
            category = notification.payload.get("category", "misc")
            grouped[category].append(notification)

        html = _render_digest(grouped)
        send_email("[Deal Scout] Daily Digest", html)

        for notification in notifications:
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            sent += 1
    return {"sent": sent}
