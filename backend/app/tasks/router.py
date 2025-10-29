from __future__ import annotations

from fastapi import APIRouter

from app.worker import celery_app

router = APIRouter()


@router.post("/scan")
async def enqueue_scan(live: bool = False):
    task = celery_app.send_task(
        "app.tasks.scan_all.run_scan_all", kwargs={"live": bool(live)}
    )
    return {"task_id": task.id, "live": bool(live)}


@router.post("/recompute-comps")
async def enqueue_comps():
    task = celery_app.send_task("app.tasks.refresh_comps.refresh_comps_task")
    return {"task_id": task.id}


@router.post("/notify")
async def enqueue_notify():
    task = celery_app.send_task("app.tasks.notify.send_notifications")
    return {"task_id": task.id}
