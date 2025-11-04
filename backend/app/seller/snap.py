from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.models import SnapJob, User, MyItem, CrossPost, ListingDraft
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
    progress: int = 0  # 0-100 percentage
    error_message: Optional[str] = None
    title: Optional[str]
    description: Optional[str]
    suggested_price: Optional[float]
    price_suggestion_cents: Optional[int]
    condition_guess: Optional[str]
    processed_images: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None


class ListingDraftResponse(BaseModel):
    id: int
    snap_job_id: Optional[int]
    category: str
    title: str
    description: Optional[str]
    condition: Optional[str]
    price_suggested: Optional[float]
    price_low: Optional[float]
    price_high: Optional[float]
    pricing_rationale: Optional[str]
    images: List[str] = Field(default_factory=list)
    bullet_highlights: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    status: str
    created_at: str
    updated_at: str


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
        progress=job.progress if hasattr(job, 'progress') else 0,
        error_message=job.error_message if hasattr(job, 'error_message') else None,
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
                progress=job.progress if hasattr(job, 'progress') else 0,
                error_message=job.error_message if hasattr(job, 'error_message') else None,
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

    # Convert condition string to enum
    from app.core.models import Condition as ConditionEnum
    try:
        condition_enum = ConditionEnum(snap_job.condition_guess) if snap_job.condition_guess else ConditionEnum.good
    except (ValueError, KeyError):
        condition_enum = ConditionEnum.good

    # Create MyItem from snap job
    my_item = MyItem(
        user_id=current_user.id,
        title=snap_job.suggested_title or "Untitled Item",
        price=request.price or snap_job.suggested_price or 0,
        condition=condition_enum,
        category=snap_job.detected_category or "other",
        attributes={
            "description": snap_job.suggested_description or "",
            "images": snap_job.processed_images or [],
            **(snap_job.detected_attributes or {}),
        },
        status="active",
    )
    db.add(my_item)
    db.flush()

    # Create cross-post record for each platform
    cross_post = CrossPost(
        my_item_id=my_item.id,
        platform=request.platforms[0] if request.platforms else "ebay",  # Use first platform
        status="pending",
        listing_url="",  # Will be populated when posted
        meta={
            "notes": request.notes,
            "all_platforms": request.platforms,
        },
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


@router.get("/drafts", response_model=List[ListingDraftResponse])
async def list_drafts(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, description="Filter by status: draft, published, archived"),
    db: Session = Depends(get_db),
):
    """List listing drafts for the current user."""
    query = db.query(ListingDraft).filter(ListingDraft.user_id == current_user.id)

    # Apply status filter if provided
    if status_filter:
        query = query.filter(ListingDraft.status == status_filter)

    drafts = query.order_by(ListingDraft.created_at.desc()).limit(limit).all()

    responses: List[ListingDraftResponse] = []
    for draft in drafts:
        responses.append(
            ListingDraftResponse(
                id=draft.id,
                snap_job_id=draft.snap_job_id,
                category=draft.category,
                title=draft.title,
                description=draft.description,
                condition=draft.condition.value if draft.condition else None,
                price_suggested=draft.price_suggested,
                price_low=draft.price_low,
                price_high=draft.price_high,
                pricing_rationale=draft.pricing_rationale,
                images=draft.images or [],
                bullet_highlights=draft.bullet_highlights or [],
                tags=draft.tags or [],
                status=draft.status,
                created_at=draft.created_at.isoformat() if draft.created_at else "",
                updated_at=draft.updated_at.isoformat() if draft.updated_at else "",
            )
        )

    return responses


@router.get("/drafts/{draft_id}", response_model=ListingDraftResponse)
async def get_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific listing draft by ID."""
    draft = db.query(ListingDraft).filter(ListingDraft.id == draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Verify ownership
    if current_user.role.value != "admin" and draft.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return ListingDraftResponse(
        id=draft.id,
        snap_job_id=draft.snap_job_id,
        category=draft.category,
        title=draft.title,
        description=draft.description,
        condition=draft.condition.value if draft.condition else None,
        price_suggested=draft.price_suggested,
        price_low=draft.price_low,
        price_high=draft.price_high,
        pricing_rationale=draft.pricing_rationale,
        images=draft.images or [],
        bullet_highlights=draft.bullet_highlights or [],
        tags=draft.tags or [],
        status=draft.status,
        created_at=draft.created_at.isoformat() if draft.created_at else "",
        updated_at=draft.updated_at.isoformat() if draft.updated_at else "",
    )
