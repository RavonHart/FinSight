import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.dependencies import get_current_active_user
from app.db.models.users import User
from app.db.models.portfolios import Asset
from app.domains.portfolios.schemas import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    HoldingCreate,
    HoldingUpdate,
    HoldingResponse,
    TransactionCreate,
    TransactionResponse,
    PortfolioAnalyticsResponse,
    AssetResponse,
)
from app.domains.portfolios.service import (
    create_portfolio,
    list_portfolios,
    get_portfolio,
    update_portfolio,
    delete_portfolio,
    list_holdings,
    create_or_update_holding,
    update_holding,
    delete_holding,
    record_transaction,
    list_transactions,
    get_portfolio_analytics,
)

portfolio_router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


@portfolio_router.get("", response_model=List[PortfolioResponse])
async def list_portfolios_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all manual and virtual portfolios owned by the active user (§20)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_portfolios(db, user_uuid)


@portfolio_router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio_endpoint(
    data: PortfolioCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new virtual or manual portfolio (§20)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await create_portfolio(db, user_uuid, data)


@portfolio_router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio_endpoint(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves metadata for a specific portfolio."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_portfolio(db, user_uuid, portfolio_id)


@portfolio_router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio_endpoint(
    portfolio_id: uuid.UUID,
    data: PortfolioUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates portfolio name or base currency."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await update_portfolio(db, user_uuid, portfolio_id, data)


@portfolio_router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_endpoint(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a portfolio and all associated holdings and transactions."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    await delete_portfolio(db, user_uuid, portfolio_id)
    return None


# ---------------------------------------------------------------------------
# Holdings Endpoints
# ---------------------------------------------------------------------------

@portfolio_router.get("/{portfolio_id}/holdings", response_model=List[HoldingResponse])
async def list_holdings_endpoint(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists holdings for a portfolio with current values and unrealized returns (§20)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_holdings(db, user_uuid, portfolio_id)


@portfolio_router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def create_holding_endpoint(
    portfolio_id: uuid.UUID,
    data: HoldingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Adds a holding to the portfolio, auto-resolving reference asset metadata (§20)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await create_or_update_holding(db, user_uuid, portfolio_id, data)


@portfolio_router.put("/{portfolio_id}/holdings/{holding_id}", response_model=HoldingResponse)
async def update_holding_endpoint(
    portfolio_id: uuid.UUID,
    holding_id: uuid.UUID,
    data: HoldingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates quantity or cost basis for an existing holding (§20)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await update_holding(db, user_uuid, portfolio_id, holding_id, data)


@portfolio_router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding_endpoint(
    portfolio_id: uuid.UUID,
    holding_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Removes a holding from a portfolio (§20)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    await delete_holding(db, user_uuid, portfolio_id, holding_id)
    return None


# ---------------------------------------------------------------------------
# Transactions Endpoints
# ---------------------------------------------------------------------------

@portfolio_router.get("/{portfolio_id}/transactions", response_model=List[TransactionResponse])
async def list_transactions_endpoint(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists chronological transaction history for a portfolio (§20)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_transactions(db, user_uuid, portfolio_id)


@portfolio_router.post("/{portfolio_id}/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def record_transaction_endpoint(
    portfolio_id: uuid.UUID,
    data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Records a buy/sell transaction with client idempotency and syncs holdings (§20, §45)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await record_transaction(db, user_uuid, portfolio_id, data)


# ---------------------------------------------------------------------------
# Analytics Endpoint
# ---------------------------------------------------------------------------

@portfolio_router.get("/{portfolio_id}/analytics", response_model=PortfolioAnalyticsResponse)
async def get_portfolio_analytics_endpoint(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Computes deterministic portfolio analytics:
    Total valuation, net cost basis, absolute return, asset allocation weights,
    sector exposure distribution, concentration HHI, and XIRR rate of return (§19, §20).
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_portfolio_analytics(db, user_uuid, portfolio_id)
