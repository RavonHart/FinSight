from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logging import logger

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)

async_session_factory = AsyncSessionLocal

# Sync engine for Celery / Alembic migrations
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Standard database session with bypass_rls=true for unauthenticated/system endpoints."""
    async with AsyncSessionLocal() as session:
        try:
            # Set system bypass for internal queries that don't belong to a specific user
            await session.execute(text("SELECT set_config('app.bypass_rls', 'true', true)"))
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_user_db(user_id: str, is_admin: bool = False) -> AsyncGenerator[AsyncSession, None]:
    """User-scoped database session setting PostgreSQL RLS context variables (§11, §30)."""
    async with AsyncSessionLocal() as session:
        try:
            # Set request-scoped RLS session variables using PostgreSQL set_config
            await session.execute(
                text("SELECT set_config('app.current_user_id', :user_id, true)"),
                {"user_id": str(user_id)}
            )
            admin_val = "true" if is_admin else "false"
            await session.execute(
                text("SELECT set_config('app.is_admin', :is_admin, true)"),
                {"is_admin": admin_val}
            )
            await session.execute(text("SELECT set_config('app.bypass_rls', 'false', true)"))
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False


async def check_database_detailed_health() -> dict:
    """Detailed health probe checking connectivity, vector extension, and pool stats (§36)."""
    try:
        async with AsyncSessionLocal() as session:
            r1 = await session.execute(text("SELECT 1"))
            db_ok = r1.scalar() == 1

            r2 = await session.execute(
                text("SELECT count(*) FROM pg_extension WHERE extname = 'vector'")
            )
            vector_ok = (r2.scalar() or 0) > 0

        pool = async_engine.pool
        checked_out = pool.checkedout()
        pool_size = pool.size()
        checked_in = pool.checkedin()
        raw_overflow = pool.overflow()

        # In SQLAlchemy QueuePool, pool.overflow() = checked_out - size.
        # This formula returns negative integers when checked-out capacity is below base pool size
        # (e.g. -9 indicates size=10, checked_out=1, leaving 9 base slots available).
        # We expose overflow_active (clamped >= 0) and available_capacity for intuitive 3am on-call operations,
        # while preserving raw_overflow and a convention_note for telemetry precision.
        overflow_active = max(0, raw_overflow)
        max_overflow = getattr(pool, "max_overflow", lambda: 10)() if hasattr(pool, "max_overflow") else 10
        available_capacity = max(0, (pool_size + max_overflow) - checked_out)

        pool_stats = {
            "size": pool_size,
            "checked_in": checked_in,
            "checked_out": checked_out,
            "overflow": overflow_active,
            "available_capacity": available_capacity,
            "raw_overflow": raw_overflow,
            "convention_note": "raw_overflow represents (checked_out - size) per SQLAlchemy QueuePool; negative indicates unused base capacity",
        }

        return {
            "healthy": db_ok,
            "vector_extension": "ok" if vector_ok else "missing",
            "connection_pool": pool_stats,
        }
    except Exception as e:
        logger.warning(f"Detailed database check failed: {e}")
        return {
            "healthy": False,
            "vector_extension": "error",
            "connection_pool": {"error": str(e)},
        }

