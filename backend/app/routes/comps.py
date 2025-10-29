"""API routes for comparable pricing data."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.core.models import Comp
from app.schemas.comp import CompOut, CompCreate
from app.schemas.common import PageResponse, PageMeta

router = APIRouter(prefix="/comps", tags=["comps"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=PageResponse[CompOut])
async def list_comps(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    source: Optional[str] = None,
) -> PageResponse[CompOut]:
    """List comparable pricing data."""
    query = db.query(Comp)

    if category:
        query = query.filter(Comp.category == category)
    if source:
        query = query.filter(Comp.source == source)

    total = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return PageResponse[CompOut](
        meta=PageMeta(page=page, size=size, total=total),
        items=[CompOut.model_validate(item) for item in items],
    )


@router.get("/category/{category}", response_model=list[CompOut])
async def get_comps_by_category(
    category: str, db: Session = Depends(get_db)
) -> list[CompOut]:
    """Get comps for a specific category."""
    comps = db.query(Comp).filter(Comp.category == category).all()
    if not comps:
        raise HTTPException(
            status_code=404, detail=f"No comps found for category '{category}'"
        )
    return [CompOut.model_validate(comp) for comp in comps]


@router.get("/{comp_id}", response_model=CompOut)
async def get_comp(comp_id: int, db: Session = Depends(get_db)) -> CompOut:
    """Get a specific comp by ID."""
    comp = db.query(Comp).filter(Comp.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Comp {comp_id} not found")
    return CompOut.model_validate(comp)


@router.post("", response_model=CompOut, status_code=201)
async def create_comp(
    payload: CompCreate, db: Session = Depends(get_db)
) -> CompOut:
    """Create a new comp entry."""
    comp = Comp(**payload.model_dump(by_alias=True))
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return CompOut.model_validate(comp)


@router.delete("/{comp_id}", status_code=204)
async def delete_comp(comp_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a comp entry."""
    comp = db.query(Comp).filter(Comp.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Comp {comp_id} not found")

    db.delete(comp)
    db.commit()
