"""API routes for user's items."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.core.models import MyItem, User
from app.core.auth import require_seller
from app.core.errors import NotFoundError
from app.schemas.my_item import MyItemOut, MyItemCreate, MyItemUpdate
from app.schemas.common import PageResponse, PageMeta

router = APIRouter(prefix="/my-items", tags=["my-items"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=PageResponse[MyItemOut])
async def list_my_items(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    _: User = Depends(require_seller),
) -> PageResponse[MyItemOut]:
    """List user's items with pagination (seller only)."""
    query = db.query(MyItem)

    if status:
        query = query.filter(MyItem.status == status)
    if category:
        query = query.filter(MyItem.category == category)

    total = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return PageResponse[MyItemOut](
        meta=PageMeta(page=page, size=size, total=total),
        items=[MyItemOut.model_validate(item) for item in items],
    )


@router.get("/{item_id}", response_model=MyItemOut)
async def get_my_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_seller),
) -> MyItemOut:
    """Get a specific item by ID (seller only)."""
    item = db.query(MyItem).filter(MyItem.id == item_id).first()
    if not item:
        raise NotFoundError(resource="MyItem", resource_id=item_id)
    return MyItemOut.model_validate(item)


@router.post("", response_model=MyItemOut, status_code=201)
async def create_my_item(
    payload: MyItemCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_seller),
) -> MyItemOut:
    """Create a new item (seller only)."""
    item = MyItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return MyItemOut.model_validate(item)


@router.patch("/{item_id}", response_model=MyItemOut)
async def update_my_item(
    item_id: int,
    payload: MyItemUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_seller),
) -> MyItemOut:
    """Update an item (seller only)."""
    item = db.query(MyItem).filter(MyItem.id == item_id).first()
    if not item:
        raise NotFoundError(resource="MyItem", resource_id=item_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return MyItemOut.model_validate(item)


@router.delete("/{item_id}", status_code=204)
async def delete_my_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_seller),
) -> None:
    """Delete an item (seller only)."""
    item = db.query(MyItem).filter(MyItem.id == item_id).first()
    if not item:
        raise NotFoundError(resource="MyItem", resource_id=item_id)

    db.delete(item)
    db.commit()
