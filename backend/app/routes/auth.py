"""Authentication endpoints for user registration, login, and token management."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.core.db import SessionLocal
from app.core.models import User
from app.core.errors import ConflictError, ValidationError, ErrorDetail, NotFoundError
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserOut,
    TokenResponse,
    TokenRefreshRequest,
    PasswordChangeRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    """Register a new user account."""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise ConflictError(message=f"Username '{payload.username}' is already taken")

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise ConflictError(message=f"Email '{payload.email}' is already registered")

    # Create new user
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create tokens
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """Login with username and password."""
    # Find user by username
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: TokenRefreshRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    """Refresh access token using refresh token."""
    # Decode refresh token
    token_data = decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Get user
    user_id = token_data.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError(resource="User", resource_id=user_id)

    # Create new access token
    new_token_data = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
    }
    access_token = create_access_token(new_token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=payload.refresh_token,  # Keep the same refresh token
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """Get current user information."""
    return UserOut.model_validate(current_user)


@router.post("/change-password", response_model=dict)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Change user password."""
    # Verify current password
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Verify new password and confirmation match
    if payload.new_password != payload.confirm_password:
        raise ValidationError(
            message="New passwords do not match",
            details=[
                ErrorDetail(
                    field="confirm_password",
                    message="Passwords do not match",
                )
            ],
        )

    # Prevent reusing the same password
    if verify_password(payload.new_password, current_user.password_hash):
        raise ValidationError(
            message="New password cannot be the same as current password"
        )

    # Update password
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.post("/logout", response_model=dict)
async def logout(current_user: User = Depends(get_current_user)) -> dict:
    """Logout (client-side token deletion)."""
    # Note: JWT tokens are stateless, so logout is primarily client-side
    # In production, you might add the token to a blacklist
    return {"message": "Logged out successfully"}
