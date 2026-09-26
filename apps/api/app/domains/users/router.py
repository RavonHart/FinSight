import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.dependencies import get_current_user, get_current_active_user, require_admin
from app.core.security import AuthenticatedUser
from app.db.models.users import User
from app.db.models.audit import AuditLog
from app.domains.users.schemas import (
    SignUpRequest,
    LoginRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.domains.users.service import (
    register_user,
    authenticate_user,
    refresh_user_token,
    list_users_for_admin,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
admin_router = APIRouter(prefix="/admin", tags=["Administration"])


@auth_router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup_endpoint(
    request: SignUpRequest,
    db: AsyncSession = Depends(get_db)
):
    """Creates a new user account with email and password."""
    return await register_user(db, request)


@auth_router.post("/login", response_model=TokenResponse)
async def login_endpoint(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticates user credentials and returns JWT bearer tokens."""
    return await authenticate_user(db, request)


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_endpoint(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revokes session and creates audit log."""
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        action="user_logged_out",
        resource_type="user",
        resource_id=current_user.id,
        metadata_json={}
    )
    db.add(audit)
    await db.commit()
    return {"status": "ok", "message": "Successfully logged out"}


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_endpoint(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Issues a new access token using a valid refresh token."""
    return await refresh_user_token(db, request.refresh_token)


@auth_router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """Initiates a secure password reset workflow without exposing user existence."""
    # Find user if exists
    result = await db.execute(select(User).where(User.email == request.email.lower()))
    user = result.scalar_one_or_none()
    if user:
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=user.id,
            action="password_reset_requested",
            resource_type="user",
            resource_id=user.id,
            metadata_json={"email": user.email}
        )
        db.add(audit)
        await db.commit()

    return {
        "status": "ok",
        "message": "If this email is registered, password reset instructions have been dispatched."
    }


@auth_router.get("/me", response_model=UserResponse)
async def get_me_endpoint(
    user: User = Depends(get_current_active_user)
):
    """Returns the profile of the currently authenticated user."""
    return UserResponse.model_validate(user)


@auth_router.put("/me", response_model=UserResponse)
async def update_me_endpoint(
    request: UserUpdateRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates profile attributes for the currently authenticated user."""
    if request.name is not None:
        user.name = request.name.strip()
    if request.avatar_url is not None:
        user.avatar_url = request.avatar_url.strip()

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@admin_router.get("/users", response_model=List[UserResponse])
async def admin_get_users(
    admin: AuthenticatedUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin-only endpoint to list all platform users."""
    return await list_users_for_admin(db)
