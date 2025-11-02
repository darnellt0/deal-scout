from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.models import SnapJob, User, MyItem, CrossPost, Condition
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

    # Enqueue processing task
    celery_app.send_task("app.tasks.process_snap.process_snap_job", args=[job.id])
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
    condition_value = snap_job.condition_guess or "good"
    condition_enum = (
        Condition(condition_value)
        if condition_value in Condition._value2member_map_
        else Condition.good
    )

    my_item = MyItem(
        user_id=current_user.id,
        title=snap_job.suggested_title or "Untitled Item",
        category=snap_job.detected_category or "other",
        attributes=snap_job.detected_attributes or {},
        condition=condition_enum,
        price=request.price or snap_job.suggested_price or 0,
        status="active",
    )
    db.add(my_item)
    db.flush()

    created_cross_posts: List[CrossPost] = []
    for platform in request.platforms:
        cross_post = CrossPost(
            my_item_id=my_item.id,
            platform=platform,
            listing_url="",
            status="pending",
            meta={
                "notes": request.notes or "",
                "snap_job_id": snap_job.id,
            },
        )
        db.add(cross_post)
        created_cross_posts.append(cross_post)

    snap_job.status = "published"
    db.commit()

    primary_cross_post = created_cross_posts[0]

    return CrossPostResponse(
        cross_post_id=primary_cross_post.id,
        item_id=my_item.id,
        platforms=request.platforms,
        status=primary_cross_post.status,
        created_at=primary_cross_post.created_at.isoformat()
        if primary_cross_post.created_at
        else None,
    )


@router.delete("/snap/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snap_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a snap draft owned by the current user."""
    snap_job = db.query(SnapJob).filter(SnapJob.id == job_id).first()
    if not snap_job:
        raise HTTPException(status_code=404, detail="Snap job not found")
    if snap_job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if snap_job.status == "published":
        raise HTTPException(
            status_code=400,
            detail="Published listings cannot be deleted",
        )
    db.delete(snap_job)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
