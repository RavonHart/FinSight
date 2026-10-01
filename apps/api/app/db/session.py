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
