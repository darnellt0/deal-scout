from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import ensure_role_from_path
from app.db.session import get_db

router = APIRouter(prefix="/seller", tags=["seller"])


@router.post("/listings")
def create_listing(
    payload: dict,
    user=Depends(ensure_role_from_path()),
    db: Session = Depends(get_db),
):
    return {"ok": True, "role": "seller"}
