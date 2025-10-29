"""API routes for orders."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.core.models import Order
from app.core.errors import NotFoundError
from app.schemas.order import OrderOut, OrderCreate, OrderUpdate
from app.schemas.common import PageResponse, PageMeta

router = APIRouter(prefix="/orders", tags=["orders"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=PageResponse[OrderOut])
async def list_orders(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
) -> PageResponse[OrderOut]:
    """List orders with pagination."""
    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return PageResponse[OrderOut](
        meta=PageMeta(page=page, size=size, total=total),
        items=[OrderOut.model_validate(item) for item in items],
    )


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderOut:
    """Get a specific order by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise NotFoundError(resource="Order", resource_id=order_id)
    return OrderOut.model_validate(order)


@router.post("", response_model=OrderOut, status_code=201)
async def create_order(
    payload: OrderCreate, db: Session = Depends(get_db)
) -> OrderOut:
    """Create a new order."""
    order = Order(**payload.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(order)


@router.patch("/{order_id}", response_model=OrderOut)
async def update_order(
    order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)
) -> OrderOut:
    """Update an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise NotFoundError(resource="Order", resource_id=order_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(order)


@router.delete("/{order_id}", status_code=204)
async def delete_order(order_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise NotFoundError(resource="Order", resource_id=order_id)

    db.delete(order)
    db.commit()
