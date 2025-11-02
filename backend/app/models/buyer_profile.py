from sqlalchemy import Column, Integer, ForeignKey

from app.core.models import Base


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    search_radius_km = Column(Integer, default=25)
    price_min_cents = Column(Integer, nullable=True)
    price_max_cents = Column(Integer, nullable=True)
