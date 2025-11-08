from __future__ import annotations

from datetime import datetime, timezone

from celery import shared_task

from app.buyer.search import run_scan
from app.config import get_settings
from app.core.db import get_session
from app.core.models import Notification
from app.notify.channels import send_discord, send_email, send_sms


def _compose_email(match) -> str:
    image_block = (
        f'<img src="{match.thumbnail_url}" alt="{match.title}" style="max-width:480px;border-radius:8px;" />'
        if match.thumbnail_url
        else ""
    )
    quick_message = f"<blockquote>{match.auto_message}</blockquote>"
    return f"""
    <h2 style="margin-bottom:4px;">{match.title}</h2>
    <p style="margin:0;color:#555;">${match.price:.0f} · Score {match.deal_score} · {match.distance_mi} mi away</p>
    <p style="margin-top:12px;">Source: {match.source.title()} · Category: {match.category}</p>
    {image_block}
    <p><a href="{match.url}">Open Listing</a></p>
    <h3>Quick Message</h3>
    {quick_message}
    """


@shared_task(name="app.tasks.scan_all.run_scan_all")
def run_scan_all(live: bool = False):
    settings = get_settings()
    use_live = bool(live) or not settings.demo_mode
    matches = run_scan(use_live=use_live)
    created = 0
    with get_session() as session:
        for match in matches:
            payload = {
                "title": match.title,
                "price": match.price,
                "deal_score": match.deal_score,
                "distance_mi": match.distance_mi,
                "thumbnail_url": match.thumbnail_url,
                "url": match.url,
                "auto_message": match.auto_message,
                "source": match.source,
                "condition": match.condition,
                "category": match.category,
            }
            channel = "digest"
            notification_status = "pending"
            sent_at = None

            instant = (
                match.is_free
                and match.condition in {"good", "great", "excellent"}
                and match.distance_mi <= settings.default_radius_mi
            )

            if instant:
                subject = f"[Deal Scout] Free find: {match.title}"
                html = _compose_email(match)
                send_email(subject, html)
                send_discord(
                    f"Free deal spotted: {match.title}",
                    embed={"title": match.title, "url": match.url},
                )
                send_sms(f"Free: {match.title} ({match.distance_mi} mi) {match.url}")
                notification_status = "sent"
                sent_at = datetime.now(timezone.utc)
                channel = "instant"
            elif match.deal_score >= 75:
                channel = "digest"
            else:
                continue

            notification = Notification(
                listing_id=match.id,
                channel=channel,
                payload=payload,
                status=notification_status,
                sent_at=sent_at,
            )
            session.add(notification)
            created += 1
    return {"matches": len(matches), "notifications": created}
