from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.db import get_session
from app.core.models import SnapJob
from app.worker import celery_app

router = APIRouter()


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


def _exposed_urls(urls: List[str]) -> List[str]:
    allowed_prefixes = ("http://", "https://", "/static/")
    return [url for url in urls if url.startswith(allowed_prefixes)]


@router.post("/snap", response_model=SnapResponse)
async def create_snap(request: SnapRequest):
    if not request.photos:
        raise HTTPException(status_code=422, detail="At least one photo is required.")

    with get_session() as session:
        job = SnapJob(
            input_photos=request.photos,
            status="queued",
            source=request.source,
        )
        session.add(job)
        session.flush()
        celery_app.send_task("app.tasks.process_snap.process_snap_job", args=[job.id])
        return SnapResponse(job_id=job.id, status=job.status)


@router.get("/snap/{job_id}", response_model=SnapStatusResponse)
async def get_snap_status(job_id: int):
    with get_session() as session:
        job = session.get(SnapJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Snap job not found.")
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
        )


@router.get("/snap", response_model=List[SnapStatusResponse])
async def list_snap_jobs():
    with get_session() as session:
        jobs = session.query(SnapJob).order_by(SnapJob.created_at.desc()).all()
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
                )
            )
        return responses
