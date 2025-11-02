from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.models.buyer_profile import BuyerProfile
from app.models.role import Role
from app.models.seller_profile import SellerProfile
from app.models.user import User
from app.db.session import get_db

AUTO_ENABLE_BUYER = True
AUTO_ENABLE_SELLER = True


def ensure_role_from_path():
    def _dep(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> User:
        db_user = db.get(User, user.id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        mode = getattr(request.state, "user_mode", None)
        if mode is None:
            return db_user

        if mode in db_user.role_names:
            return db_user

        if mode == "buyer" and not AUTO_ENABLE_BUYER:
            raise HTTPException(status_code=403, detail="Enable 'buyer' first.")
        if mode == "seller" and not AUTO_ENABLE_SELLER:
            raise HTTPException(status_code=403, detail="Enable 'seller' first.")

        role = db.query(Role).filter(Role.name == mode).first()
        if not role:
            role = Role(name=mode)
            db.add(role)
            db.flush()

        db_user.roles.append(role)

        if mode == "buyer" and not db.get(BuyerProfile, db_user.id):
            db.add(BuyerProfile(user_id=db_user.id))
        if mode == "seller" and not db.get(SellerProfile, db_user.id):
            db.add(SellerProfile(user_id=db_user.id))

        db.commit()
        db.refresh(db_user)
        return db_user

    return _dep
