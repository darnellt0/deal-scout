"""JWT authentication and authorization utilities."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.requests import Request
import jwt
from jwt.exceptions import InvalidTokenError
import bcrypt
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.models import User, UserRole

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", 60))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_DAYS", 7))
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_PASSWORD_RESET_MINUTES", 30))

# HTTP Bearer for FastAPI dependency
security = HTTPBearer()


class TokenData:
    """JWT token payload data."""
    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        role: str,
        is_active: bool = True,
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.is_active = is_active


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Bcrypt has a 72-byte limit, so truncate if needed
    if len(password.encode()) > 72:
        password = password[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # Bcrypt has a 72-byte limit
    if len(plain_password.encode()) > 72:
        plain_password = plain_password[:72]
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_password_reset_token(user_id: int, email: str) -> str:
    """Create a JWT token for password reset."""
    to_encode = {
        "user_id": user_id,
        "email": email,
        "type": "password_reset",
    }
    expire = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_email_verification_token(user_id: int, email: str) -> str:
    """Create a JWT token for email verification."""
    to_encode = {
        "user_id": user_id,
        "email": email,
        "type": "email_verification",
    }
    expire = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days for email verification
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (InvalidTokenError, jwt.DecodeError, jwt.ExpiredSignatureError):
        return None


async def get_current_user(request: Request) -> User:
    """Get current authenticated user from JWT token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get database session
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return user
    finally:
        db.close()


async def get_current_user_optional(request: Request) -> Optional[User]:
    """Get current user if authenticated, else None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        return await get_current_user(request)
    except HTTPException:
        return None


def require_role(*roles: UserRole):
    """Dependency to require specific user roles."""
    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role.value}' does not have access",
            )
        return current_user

    return check_role


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_seller(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require seller or admin role."""
    if current_user.role not in (UserRole.seller, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller access required",
        )
    return current_user
