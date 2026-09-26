from typing import AsyncGenerator, Optional
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings
from app.core.security import AuthenticatedUser, verify_supabase_jwt


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()


async def check_redis_health() -> bool:
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        response = await client.ping()
        await client.close()
        return response is True or response == "PONG"
    except Exception:
        return False


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> AuthenticatedUser:
    if not authorization:
        # If in development and testing without token, return a local mock user
        if not settings.is_production:
            return AuthenticatedUser(
                user_id="00000000-0000-0000-0000-000000000001",
                email="dev@finsight.local",
                is_admin=True
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme; Expected 'Bearer <token>'"
        )

    return verify_supabase_jwt(parts[1])


async def require_admin(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user
