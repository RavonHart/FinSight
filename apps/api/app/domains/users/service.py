import uuid
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.users import User
from app.db.models.audit import AuditLog
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_supabase_jwt,
)
from app.domains.users.schemas import SignUpRequest, LoginRequest, TokenResponse, UserResponse
from app.core.logging import logger


async def register_user(db: AsyncSession, request: SignUpRequest) -> TokenResponse:
    """Registers a new user with email and password, creates audit log, and generates JWT tokens."""
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == request.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists"
        )

    user = User(
        id=uuid.uuid4(),
        email=request.email.lower(),
        name=request.name.strip(),
        hashed_password=hash_password(request.password),
        auth_provider="local",
        is_active=True,
        email_verified=False,
        is_admin=False,
    )
    db.add(user)
    await db.flush()

    # Record audit log
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=user.id,
        action="user_registered",
        resource_type="user",
        resource_id=user.id,
        metadata_json={"auth_provider": "local", "email": user.email}
    )
    db.add(audit)

    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        is_admin=user.is_admin,
        auth_provider=user.auth_provider,
    )
    refresh_token = create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse.model_validate(user),
    )


async def authenticate_user(db: AsyncSession, request: LoginRequest) -> TokenResponse:
    """Authenticates credentials, generates JWT tokens, and writes audit log."""
    result = await db.execute(select(User).where(User.email == request.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        logger.warning(f"Failed authentication attempt for email: {request.email.lower()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(request.password, user.hashed_password):
        logger.warning(f"Failed password check for user ID: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended or deactivated"
        )

    # Record audit log
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=user.id,
        action="user_logged_in",
        resource_type="user",
        resource_id=user.id,
        metadata_json={"auth_provider": user.auth_provider}
    )
    db.add(audit)
    await db.commit()

    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        is_admin=user.is_admin,
        auth_provider=user.auth_provider,
    )
    refresh_token = create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse.model_validate(user),
    )


async def refresh_user_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """Validates refresh token and issues a fresh access token."""
    auth_user = verify_supabase_jwt(refresh_token)
    result = await db.execute(select(User).where(User.id == auth_user.id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token or inactive account"
        )

    new_access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        is_admin=user.is_admin,
        auth_provider=user.auth_provider,
    )
    new_refresh_token = create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse.model_validate(user),
    )


async def list_users_for_admin(db: AsyncSession, limit: int = 50, offset: int = 0) -> List[UserResponse]:
    """Admin-only query to inspect user accounts."""
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(limit).offset(offset))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]
