from typing import AsyncGenerator, Optional
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db, get_user_db
from app.core.config import settings
from app.core.security import AuthenticatedUser, verify_supabase_jwt
from app.db.models.users import User


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def check_redis_health() -> bool:
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        response = await client.ping()
        await client.aclose()
        return response is True or response == "PONG"
    except Exception:
        return False


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> AuthenticatedUser:
    """
    Extracts and validates JWT Bearer token (§11).
    Never trusts client-supplied user_id and rejects unauthenticated requests.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme; Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_supabase_jwt(parts[1])


async def get_current_active_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Resolves the authenticated user from the database or synchronizes on first login.
    Guarantees user exists in local PostgreSQL schema and is active.
    """
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()

    if not user:
        # Just-in-time synchronization for OAuth/external Supabase users
        user = User(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name or current_user.email.split("@")[0],
            auth_provider=current_user.auth_provider,
            is_admin=current_user.is_admin,
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    return user


async def require_admin(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """Restricts access to administrative endpoints (§47)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user
