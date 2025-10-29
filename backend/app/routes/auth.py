"""Authentication endpoints for user registration, login, and token management."""

import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    create_email_verification_token,
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
    UserUpdate,
    TokenResponse,
    TokenRefreshRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerification,
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

    # Send welcome email
    from app.core.email_service import get_email_service
    email_service = get_email_service()
    email_sent = email_service.send_welcome_email(
        to_email=user.email,
        username=user.username,
    )
    if not email_sent:
        logger.warning(f"Failed to send welcome email to {user.email}")

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


@router.get("/profile", response_model=UserOut)
async def get_profile(current_user: User = Depends(get_current_user)) -> UserOut:
    """Get user profile."""
    return UserOut.model_validate(current_user)


@router.put("/profile", response_model=UserOut)
async def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    """Update user profile."""
    # Reattach user to the new session
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise NotFoundError(resource="User", resource_id=current_user.id)

    # Update only provided fields
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.profile is not None:
        user.profile = payload.profile

    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/logout", response_model=dict)
async def logout(current_user: User = Depends(get_current_user)) -> dict:
    """Logout (client-side token deletion)."""
    # Note: JWT tokens are stateless, so logout is primarily client-side
    # In production, you might add the token to a blacklist
    return {"message": "Logged out successfully"}


@router.post("/request-password-reset", response_model=dict)
async def request_password_reset(
    payload: PasswordResetRequest, db: Session = Depends(get_db)
) -> dict:
    """Request a password reset token via email."""
    # Find user by email
    user = db.query(User).filter(User.email == payload.email).first()

    # Don't reveal if email exists (security best practice)
    # But still generate and return token for testing in development
    if not user:
        return {"message": "If an account exists with that email, a reset link will be sent"}

    # Create password reset token
    reset_token = create_password_reset_token(user.id, user.email)

    # Send password reset email
    from app.core.email_service import get_email_service
    email_service = get_email_service()
    email_sent = email_service.send_password_reset_email(
        to_email=user.email,
        username=user.username,
        reset_token=reset_token,
    )

    if not email_sent:
        logger.warning(f"Failed to send password reset email to {user.email}")

    return {
        "message": "If an account exists with that email, a password reset link has been sent"
    }


@router.post("/confirm-password-reset", response_model=dict)
async def confirm_password_reset(
    payload: PasswordResetConfirm, db: Session = Depends(get_db)
) -> dict:
    """Confirm password reset with token."""
    # Decode password reset token
    token_data = decode_token(payload.token)
    if not token_data or token_data.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired password reset token",
        )

    # Get user
    user_id = token_data.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError(resource="User", resource_id=user_id)

    # Update password
    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password has been reset successfully"}


@router.post("/send-email-verification", response_model=dict)
async def send_email_verification(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    """Send email verification token to current user."""
    # Create email verification token
    verification_token = create_email_verification_token(current_user.id, current_user.email)

    # Send email verification email
    from app.core.email_service import get_email_service
    email_service = get_email_service()
    email_sent = email_service.send_email_verification_email(
        to_email=current_user.email,
        username=current_user.username,
        verification_token=verification_token,
    )

    if not email_sent:
        logger.warning(f"Failed to send email verification to {current_user.email}")

    return {
        "message": "Verification link has been sent to your email"
    }


@router.post("/verify-email", response_model=EmailVerification)
async def verify_email(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> EmailVerification:
    """Verify email with verification token."""
    # Decode email verification token
    token_data = decode_token(payload.token)
    if not token_data or token_data.get("type") != "email_verification":
        return EmailVerification(
            verified=False,
            message="Invalid or expired email verification token",
        )

    # Get user
    user_id = token_data.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return EmailVerification(
            verified=False,
            message="User not found",
        )

    # Mark email as verified
    user.is_verified = True
    db.commit()

    return EmailVerification(
        verified=True,
        message="Email has been verified successfully",
    )
