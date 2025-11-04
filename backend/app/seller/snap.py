from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.models import SnapJob, User, MyItem, CrossPost
from app.core.auth import get_current_user, require_seller
from app.worker import celery_app

router = APIRouter()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SnapRequest(BaseModel):
    photos: List[str]
    notes: Optional[str] = None
    source: str = "upload"
    enable_crosspost_prep: bool = False
    crosspost_platforms: Optional[List[str]] = None


class SnapResponse(BaseModel):
    job_id: int
    status: str


class SnapStatusResponse(BaseModel):
    job_id: int
    status: str
    title: Optional[str]
    description: Optional[str]
    suggested_price: Optional[float]
    price_suggestion_cents: Optional[int]
    condition_guess: Optional[str]
    processed_images: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None


class CrossPostRequest(BaseModel):
    snap_job_id: int
    platforms: List[str] = Field(default_factory=lambda: ["ebay"])
    price: Optional[float] = None
    notes: Optional[str] = None


class CrossPostResponse(BaseModel):
    cross_post_id: int
    item_id: int
    platforms: List[str]
    status: str
    created_at: str


def _exposed_urls(urls: List[str]) -> List[str]:
    allowed_prefixes = ("http://", "https://", "/static/")
    return [url for url in urls if url.startswith(allowed_prefixes)]


@router.post("/snap", response_model=SnapResponse)
async def create_snap(
    request: SnapRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new Snap Studio job (authenticated users only)."""
    if not request.photos:
        raise HTTPException(status_code=422, detail="At least one photo is required.")

    job = SnapJob(
        input_photos=request.photos,
        status="queued",
        source=request.source,
        user_id=current_user.id,
    )
    db.add(job)
    db.flush()

    # Enqueue processing task with optional cross-post prep
    celery_app.send_task(
        "app.tasks.process_snap.process_snap_job",
        args=[job.id],
        kwargs={
            "enable_crosspost_prep": request.enable_crosspost_prep,
            "platforms": request.crosspost_platforms,
        }
    )
    db.commit()

    return SnapResponse(job_id=job.id, status=job.status)


@router.get("/snap/{job_id}", response_model=SnapStatusResponse)
async def get_snap_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get status of a Snap Studio job."""
    job = db.query(SnapJob).filter(SnapJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Snap job not found.")

    # Allow access if user is admin or job owner
    if current_user.role.value != "admin" and job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return SnapStatusResponse(
        job_id=job.id,
        status=job.status,
        title=job.suggested_title or job.title_suggestion,
        description=job.suggested_description or job.description_suggestion,
        suggested_price=job.suggested_price,
        price_suggestion_cents=job.price_suggestion_cents,
        condition_guess=job.condition_guess,
        processed_images=job.processed_images or [],
        images=_exposed_urls(job.input_photos),
        created_at=job.created_at.isoformat() if job.created_at else None,
    )


@router.get("/snap", response_model=List[SnapStatusResponse])
async def list_snap_jobs(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List Snap Studio jobs for current user."""
    # Admins see all jobs, other users see only their own
    query = db.query(SnapJob)
    if current_user.role.value != "admin":
        query = query.filter(SnapJob.user_id == current_user.id)

    jobs = query.order_by(SnapJob.created_at.desc()).limit(limit).all()

    responses: List[SnapStatusResponse] = []
    for job in jobs:
        responses.append(
            SnapStatusResponse(
                job_id=job.id,
                status=job.status,
                title=job.suggested_title or job.title_suggestion,
                description=job.suggested_description or job.description_suggestion,
                suggested_price=job.suggested_price,
                price_suggestion_cents=job.price_suggestion_cents,
                condition_guess=job.condition_guess,
                processed_images=job.processed_images or [],
                images=_exposed_urls(job.input_photos),
                created_at=job.created_at.isoformat() if job.created_at else None,
            )
        )
    return responses


@router.post("/snap/{job_id}/publish", response_model=CrossPostResponse)
async def publish_snap_to_marketplace(
    job_id: int,
    request: CrossPostRequest,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    """Publish a Snap Studio job to one or more marketplaces (cross-posting)."""
    # Get the snap job
    snap_job = db.query(SnapJob).filter(SnapJob.id == job_id).first()
    if not snap_job:
        raise HTTPException(status_code=404, detail="Snap job not found")

    # Verify ownership
    if snap_job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create MyItem from snap job
    my_item = MyItem(
        user_id=current_user.id,
        title=snap_job.suggested_title or "Untitled Item",
        description=snap_job.suggested_description or "",
        price=request.price or snap_job.suggested_price or 0,
        condition=snap_job.condition_guess,
        category=snap_job.detected_category or "other",
        images=snap_job.processed_images or [],
        status="active",
    )
    db.add(my_item)
    db.flush()

    # Create cross-post record
    cross_post = CrossPost(
        item_id=my_item.id,
        user_id=current_user.id,
        platforms=request.platforms,
        status="pending",
        notes=request.notes,
    )
    db.add(cross_post)
    db.flush()

    # Enqueue cross-posting task
    celery_app.send_task(
        "app.tasks.cross_post.post_to_marketplaces",
        args=[cross_post.id],
    )

    db.commit()

    return CrossPostResponse(
        cross_post_id=cross_post.id,
        item_id=my_item.id,
        platforms=request.platforms,
        status=cross_post.status,
        created_at=cross_post.created_at.isoformat() if cross_post.created_at else None,
    )
