"""Schemas for User model and authentication."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.models import UserRole


class UserBase(BaseModel):
    """Base user fields."""
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    first_name: Optional[str] = Field(None, max_length=128)
    last_name: Optional[str] = Field(None, max_length=128)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=72)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(...)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, max_length=128)
    last_name: Optional[str] = Field(None, max_length=128)
    profile: Optional[dict] = Field(default=None)


class UserOut(BaseModel):
    """Output schema for user (without sensitive data)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole = Field(default=UserRole.buyer)
    is_active: bool = True
    is_verified: bool = False
    profile: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


class UserDetailOut(UserOut):
    """Detailed user output with all fields."""
    pass


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str = Field(...)
    refresh_token: Optional[str] = Field(None)
    token_type: str = Field(default="bearer")
    user: UserOut = Field(...)


class TokenRefreshRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str = Field(...)


class PasswordChangeRequest(BaseModel):
    """Request to change password."""
    current_password: str = Field(...)
    new_password: str = Field(..., min_length=8, max_length=72)
    confirm_password: str = Field(...)


class PasswordResetRequest(BaseModel):
    """Request to reset password via email."""
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""
    token: str = Field(...)
    new_password: str = Field(..., min_length=8, max_length=72)
