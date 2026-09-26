import uuid
import pytest
from sqlalchemy import text, select
from app.db.session import AsyncSessionLocal
from app.db.models.portfolios import Portfolio
from app.db.models.users import User


@pytest.mark.asyncio
async def test_row_level_security_tenant_isolation():
    """
    Verifies PostgreSQL RLS guarantees that queries executed under User A's session
    cannot see or modify User B's portfolios (§11, §30).
    """
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    # 1. Setup: Insert User A and User B, and User A's Portfolio (using bypass_rls=true)
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT set_config('app.bypass_rls', 'true', true)"))
        
        user_a = User(
            id=user_a_id,
            email=f"user_a_{user_a_id.hex[:6]}@example.com",
            name="User A",
            auth_provider="local"
        )
        user_b = User(
            id=user_b_id,
            email=f"user_b_{user_b_id.hex[:6]}@example.com",
            name="User B",
            auth_provider="local"
        )
        session.add_all([user_a, user_b])
        await session.flush()

        portfolio_a = Portfolio(
            id=uuid.uuid4(),
            user_id=user_a_id,
            name="User A Secret Tech Portfolio",
            base_currency="USD",
            portfolio_type="manual"
        )
        session.add(portfolio_a)
        await session.commit()

    # 2. Query as User B (RLS active for user_b_id under application role)
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET ROLE finsight_app"))
        await session.execute(text("SELECT set_config('app.bypass_rls', 'false', true)"))
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": str(user_b_id)}
        )
        await session.execute(text("SELECT set_config('app.is_admin', 'false', true)"))

        # User B queries all portfolios
        result = await session.execute(select(Portfolio))
        portfolios_seen_by_b = result.scalars().all()

        # RLS must completely hide User A's portfolio from User B!
        portfolio_ids_seen = [p.id for p in portfolios_seen_by_b]
        assert portfolio_a.id not in portfolio_ids_seen, "RLS breach: User B saw User A's portfolio!"

    # 3. Query as User A (RLS active for user_a_id under application role)
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET ROLE finsight_app"))
        await session.execute(text("SELECT set_config('app.bypass_rls', 'false', true)"))
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": str(user_a_id)}
        )
        await session.execute(text("SELECT set_config('app.is_admin', 'false', true)"))

        result = await session.execute(select(Portfolio))
        portfolios_seen_by_a = result.scalars().all()
        portfolio_ids_seen = [p.id for p in portfolios_seen_by_a]
        assert portfolio_a.id in portfolio_ids_seen, "User A should see their own portfolio under RLS!"
