from sqlalchemy import Column, Integer, Text, ForeignKey

from app.core.models import Base


class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    default_location = Column(Text, nullable=True)
    default_condition = Column(Text, nullable=True)
