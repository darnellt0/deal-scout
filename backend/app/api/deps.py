from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.models import User, UserRole
from app.core.db import SessionLocal

AUTO_ENABLE_BUYER = True
AUTO_ENABLE_SELLER = True


def ensure_role_from_path():
    def _dep(
        request: Request,
        db: Session = Depends(lambda: SessionLocal()),
        user: User = Depends(get_current_user),
    ) -> User:
        db_user = db.query(User).filter(User.id == user.id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        mode = getattr(request.state, "user_mode", None)
        if mode is None:
            db.close()
            return db_user

        # Check if user already has the required role
        if db_user.role.value == mode or db_user.role == UserRole.admin:
            db.close()
            return db_user

        # Allow mode change if auto-enable is on
        if mode == "buyer" and not AUTO_ENABLE_BUYER:
            db.close()
            raise HTTPException(status_code=403, detail="Enable 'buyer' first.")
        if mode == "seller" and not AUTO_ENABLE_SELLER:
            db.close()
            raise HTTPException(status_code=403, detail="Enable 'seller' first.")

        # Update user role to the requested mode
        if mode in [e.value for e in UserRole]:
            db_user.role = UserRole(mode)
            db.commit()
            db.refresh(db_user)

        db.close()
        return db_user

    return _dep
