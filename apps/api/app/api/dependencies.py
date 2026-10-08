import logging
import uuid
from typing import AsyncGenerator, Optional
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db, get_user_db
from app.core.config import settings
from app.core.security import AuthenticatedUser, verify_supabase_jwt
from app.db.models.users import User

logger = logging.getLogger(__name__)


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


async def check_celery_worker_health() -> dict:
    """
    Checks Celery worker availability with Redis caching (10s TTL) and fail-open semantics (§36).
    A cache-miss or slow ping defaults to 'degraded' rather than blocking or failing readiness.
    """
    cache_key = "health:celery_workers_status"
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        cached_val = await client.get(cache_key)
        if cached_val:
            await client.aclose()
            import json
            return json.loads(cached_val)

        # Cache miss: run brief ping in thread pool to avoid blocking asyncio loop
        import asyncio
        from app.workers.celery_app import celery_app

        def _ping_sync():
            try:
                # 0.5s timeout prevents long broadcast delays
                inspector = celery_app.control.inspect(timeout=0.5)
                ping_res = inspector.ping()
                return ping_res or {}
            except Exception:
                return {}

        loop = asyncio.get_running_loop()
        pings = await loop.run_in_executor(None, _ping_sync)
        worker_count = len(pings) if isinstance(pings, dict) else 0

        status_str = "ok" if worker_count > 0 else "degraded"
        if status_str == "degraded":
            logger.warning(
                "Celery worker probe detected 0 active workers (status=degraded). "
                "Readiness probe will fail-open (HTTP 200) to prevent orchestration crash loops, "
                "but operational attention is required: background research and daily scans will queue."
            )

        status_dict = {
            "status": status_str,
            "active_workers": worker_count,
            "cached": False,
        }

        # Cache in Redis with 10s TTL
        import json
        await client.set(cache_key, json.dumps(status_dict), ex=10)
        await client.aclose()
        return status_dict
    except Exception as e:
        logger.warning(
            f"Celery worker health check failed with exception: {e}. "
            "Failing-open as degraded to protect container readiness."
        )
        return {
            "status": "degraded",
            "active_workers": 0,
            "error": str(e),
            "cached": False,
        }



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
    user_uuid = uuid.UUID(current_user.id) if isinstance(current_user.id, str) else current_user.id
    result = await db.execute(select(User).where((User.id == user_uuid) | (User.email == current_user.email)))
    user = result.scalar_one_or_none()

    if not user:
        # Just-in-time synchronization for OAuth/external Supabase users
        user = User(
            id=user_uuid,
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
