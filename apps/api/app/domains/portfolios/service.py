import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.db.models.portfolios import Portfolio, Holding, Asset, Transaction
from app.db.models.audit import AuditLog
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
    AllocationItem,
    SectorExposureItem,
    ConcentrationMetrics,
)
from app.finance.engine import (
    calculate_portfolio_value,
    calculate_total_cost,
    calculate_absolute_return,
    calculate_allocation,
    calculate_sector_exposure,
    calculate_concentration,
    calculate_xirr,
)
from app.finance.rounding import round_currency, round_percent, round_ratio

# Curated reference metadata for standard market assets
DEFAULT_ASSET_METADATA = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics", "asset_type": "stock", "default_price": Decimal("225.00")},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "industry": "Software", "asset_type": "stock", "default_price": Decimal("430.00")},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors", "asset_type": "stock", "default_price": Decimal("125.00")},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "industry": "Internet Retail", "asset_type": "stock", "default_price": Decimal("185.00")},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Communication Services", "industry": "Internet Content", "asset_type": "stock", "default_price": Decimal("165.00")},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "industry": "Pharmaceuticals", "asset_type": "stock", "default_price": Decimal("160.00")},
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Financial Services", "industry": "Diversified Banking", "asset_type": "stock", "default_price": Decimal("210.00")},
    "VTI": {"name": "Vanguard Total Stock Market ETF", "sector": "Broad Market", "industry": "Blend ETF", "asset_type": "etf", "default_price": Decimal("275.00")},
    "BND": {"name": "Vanguard Total Bond Market ETF", "sector": "Fixed Income", "industry": "Bond ETF", "asset_type": "bond", "default_price": Decimal("73.50")},
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "sector": "Large Cap Blend", "industry": "Index ETF", "asset_type": "etf", "default_price": Decimal("570.00")},
    "QQQ": {"name": "Invesco QQQ Trust", "sector": "Technology Growth", "industry": "Tech ETF", "asset_type": "etf", "default_price": Decimal("485.00")},
}


async def get_or_create_asset(
    db: AsyncSession,
    symbol: str,
    name: Optional[str] = None,
    asset_type: str = "stock",
    sector: Optional[str] = None,
    current_price: Optional[Decimal] = None,
) -> Asset:
    """Retrieves an existing asset by ticker or registers a new reference asset."""
    sym = symbol.strip().upper()
    result = await db.execute(select(Asset).where(Asset.symbol == sym))
    asset = result.scalar_one_or_none()

    if asset:
        return asset

    meta = DEFAULT_ASSET_METADATA.get(sym, {})
    asset_name = name or meta.get("name") or f"{sym} Corporation"
    final_sector = sector or meta.get("sector") or "Unassigned"
    final_type = meta.get("asset_type") or asset_type
    industry = meta.get("industry")

    new_asset = Asset(
        id=uuid.uuid4(),
        symbol=sym,
        name=asset_name,
        asset_type=final_type,
        exchange="NASDAQ/NYSE",
        currency="USD",
        sector=final_sector,
        industry=industry,
        metadata_json={},
    )
    db.add(new_asset)
    await db.flush()
    return new_asset


# ---------------------------------------------------------------------------
# Portfolio CRUD
# ---------------------------------------------------------------------------

async def create_portfolio(
    db: AsyncSession, user_id: uuid.UUID, data: PortfolioCreate
) -> PortfolioResponse:
    """Creates a new manual or virtual portfolio (§20)."""
    p_type = data.portfolio_type.lower()
    is_virt = data.is_virtual or (p_type == "virtual")

    portfolio = Portfolio(
        id=uuid.uuid4(),
        user_id=user_id,
        name=data.name.strip(),
        base_currency=data.base_currency.upper(),
        portfolio_type=p_type,
        is_virtual=is_virt,
    )
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)

    return PortfolioResponse.model_validate(portfolio)


async def list_portfolios(
    db: AsyncSession, user_id: uuid.UUID
) -> List[PortfolioResponse]:
    """Lists all portfolios owned by the authenticated user."""
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == user_id)
        .order_by(Portfolio.created_at.desc())
    )
    portfolios = result.scalars().all()
    return [PortfolioResponse.model_validate(p) for p in portfolios]


async def get_portfolio_entity(
    db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID
) -> Portfolio:
    """Internal helper to retrieve and verify ownership of a portfolio."""
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id, Portfolio.user_id == user_id
        )
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or access denied",
        )
    return portfolio


async def get_portfolio(
    db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID
) -> PortfolioResponse:
    portfolio = await get_portfolio_entity(db, user_id, portfolio_id)
    return PortfolioResponse.model_validate(portfolio)


async def update_portfolio(
    db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID, data: PortfolioUpdate
) -> PortfolioResponse:
    portfolio = await get_portfolio_entity(db, user_id, portfolio_id)
    if data.name is not None:
        portfolio.name = data.name.strip()
    if data.base_currency is not None:
        portfolio.base_currency = data.base_currency.upper()

    await db.commit()
    await db.refresh(portfolio)
    return PortfolioResponse.model_validate(portfolio)


async def delete_portfolio(
    db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID
) -> None:
    portfolio = await get_portfolio_entity(db, user_id, portfolio_id)
    await db.delete(portfolio)
    await db.commit()


# ---------------------------------------------------------------------------
# Holdings CRUD
# ---------------------------------------------------------------------------

async def list_holdings(
    db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID
) -> List[HoldingResponse]:
    """Lists all holdings for a portfolio with asset metadata and gain/loss."""
    await get_portfolio_entity(db, user_id, portfolio_id)

    query = (
        select(Holding, Asset)
        .join(Asset, Holding.asset_id == Asset.id)
        .where(Holding.portfolio_id == portfolio_id)
        .order_by(Asset.symbol.asc())
    )
    results = (await db.execute(query)).all()

    holdings_response = []
    for h, asset in results:
        # Recompute value dynamically (§19)
        price = h.current_price
        val = (h.quantity * price) if price is not None else None
        cost = h.quantity * h.average_cost
        gain = (val - cost) if val is not None else None
        gain_pct = (gain / cost) if (gain is not None and cost > Decimal("0")) else None

        holdings_response.append(
            HoldingResponse(
                id=h.id,
                portfolio_id=h.portfolio_id,
                asset_id=h.asset_id,
                symbol=asset.symbol,
                name=asset.name,
                asset_type=asset.asset_type,
                sector=asset.sector,
                quantity=h.quantity,
                average_cost=h.average_cost,
                current_price=h.current_price,
                current_price_as_of=h.current_price_as_of,
                current_value=val,
                unrealized_gain_loss=gain,
                unrealized_gain_loss_pct=gain_pct,
                created_at=h.created_at,
                updated_at=h.updated_at,
            )
        )

    return holdings_response


async def create_or_update_holding(
    db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID, data: HoldingCreate
) -> HoldingResponse:
    """Adds a new holding or updates an existing holding for an asset (§20)."""
    await get_portfolio_entity(db, user_id, portfolio_id)

    # Resolve default price from metadata if not supplied
    default_meta_price = DEFAULT_ASSET_METADATA.get(data.symbol.strip().upper(), {}).get("default_price")
    price = data.current_price or default_meta_price or data.average_cost

    asset = await get_or_create_asset(
        db,
        symbol=data.symbol,
        name=data.name,
        asset_type=data.asset_type or "stock",
        sector=data.sector,
        current_price=price,
    )

    # Check if holding already exists for this (portfolio_id, asset_id)
    res = await db.execute(
        select(Holding).where(
            Holding.portfolio_id == portfolio_id, Holding.asset_id == asset.id
        )
    )
    holding = res.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if holding:
        # Update existing holding
        holding.quantity = data.quantity
        holding.average_cost = data.average_cost
        if price is not None:
            holding.current_price = price
            holding.current_price_as_of = now
            holding.current_value = data.quantity * price
    else:
        # Create new holding
        holding = Holding(
            id=uuid.uuid4(),
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            quantity=data.quantity,
            average_cost=data.average_cost,
            current_price=price,
            current_price_as_of=now if price is not None else None,
            current_value=(data.quantity * price) if price is not None else None,
        )
        db.add(holding)

    await db.commit()
    await db.refresh(holding)

    val = holding.quantity * holding.current_price if holding.current_price else None
    cost = holding.quantity * holding.average_cost
    gain = (val - cost) if val is not None else None
    gain_pct = (gain / cost) if (gain is not None and cost > Decimal("0")) else None

    return HoldingResponse(
        id=holding.id,
        portfolio_id=holding.portfolio_id,
        asset_id=asset.id,
        symbol=asset.symbol,
        name=asset.name,
        asset_type=asset.asset_type,
        sector=asset.sector,
        quantity=holding.quantity,
        average_cost=holding.average_cost,
        current_price=holding.current_price,
        current_price_as_of=holding.current_price_as_of,
        current_value=val,
        unrealized_gain_loss=gain,
        unrealized_gain_loss_pct=gain_pct,
        created_at=holding.created_at,
        updated_at=holding.updated_at,
    )


async def update_holding(
    db: AsyncSession,
    user_id: uuid.UUID,
    portfolio_id: uuid.UUID,
    holding_id: uuid.UUID,
    data: HoldingUpdate,
) -> HoldingResponse:
    await get_portfolio_entity(db, user_id, portfolio_id)

    res = await db.execute(
        select(Holding, Asset)
        .join(Asset, Holding.asset_id == Asset.id)
        .where(Holding.id == holding_id, Holding.portfolio_id == portfolio_id)
    )
    item = res.first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found"
        )

    holding, asset = item
    if data.quantity is not None:
        holding.quantity = data.quantity
    if data.average_cost is not None:
        holding.average_cost = data.average_cost
    if data.current_price is not None:
        holding.current_price = data.current_price
        holding.current_price_as_of = datetime.now(timezone.utc)
        holding.current_value = holding.quantity * holding.current_price

    await db.commit()
    await db.refresh(holding)

    val = holding.quantity * holding.current_price if holding.current_price else None
    cost = holding.quantity * holding.average_cost
    gain = (val - cost) if val is not None else None
    gain_pct = (gain / cost) if (gain is not None and cost > Decimal("0")) else None

    return HoldingResponse(
        id=holding.id,
        portfolio_id=holding.portfolio_id,
        asset_id=asset.id,
        symbol=asset.symbol,
        name=asset.name,
        asset_type=asset.asset_type,
        sector=asset.sector,
        quantity=holding.quantity,
        average_cost=holding.average_cost,
        current_price=holding.current_price,
        current_price_as_of=holding.current_price_as_of,
        current_value=val,
        unrealized_gain_loss=gain,
        unrealized_gain_loss_pct=gain_pct,
        created_at=holding.created_at,
        updated_at=holding.updated_at,
    )


async def delete_holding(
    db: AsyncSession,
    user_id: uuid.UUID,
    portfolio_id: uuid.UUID,
    holding_id: uuid.UUID,
) -> None:
    await get_portfolio_entity(db, user_id, portfolio_id)
    res = await db.execute(
        select(Holding).where(
            Holding.id == holding_id, Holding.portfolio_id == portfolio_id
        )
    )
    holding = res.scalar_one_or_none()
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found"
        )
    await db.delete(holding)
    await db.commit()


# ---------------------------------------------------------------------------
# Transactions & Balance Sync
# ---------------------------------------------------------------------------

async def record_transaction(
    db: AsyncSession,
    user_id: uuid.UUID,
    portfolio_id: uuid.UUID,
    data: TransactionCreate,
) -> TransactionResponse:
    """Records a buy/sell/dividend transaction with idempotency and holding synchronization (§20, §45)."""
    await get_portfolio_entity(db, user_id, portfolio_id)

    # Idempotency check (§45)
    if data.idempotency_key:
        existing_tx = await db.execute(
            select(Transaction, Asset)
            .join(Asset, Transaction.asset_id == Asset.id)
            .where(Transaction.idempotency_key == data.idempotency_key)
        )
        existing = existing_tx.first()
        if existing:
            tx, asset = existing
            return TransactionResponse(
                id=tx.id,
                portfolio_id=tx.portfolio_id,
                asset_id=tx.asset_id,
                symbol=asset.symbol,
                transaction_type=tx.transaction_type,
                quantity=tx.quantity,
                price=tx.price,
                fees=tx.fees,
                transaction_date=tx.transaction_date,
                idempotency_key=tx.idempotency_key,
                created_at=tx.created_at,
            )

    asset = await get_or_create_asset(db, symbol=data.symbol)
    tx_type = data.transaction_type.lower()
    tx_date = data.transaction_date or datetime.now(timezone.utc)

    transaction = Transaction(
        id=uuid.uuid4(),
        portfolio_id=portfolio_id,
        asset_id=asset.id,
        transaction_type=tx_type,
        quantity=data.quantity,
        price=data.price,
        fees=data.fees,
        transaction_date=tx_date,
        idempotency_key=data.idempotency_key,
    )
    db.add(transaction)

    # Synchronize Holding balance
    holding_res = await db.execute(
        select(Holding).where(
            Holding.portfolio_id == portfolio_id, Holding.asset_id == asset.id
        )
    )
    holding = holding_res.scalar_one_or_none()

    if tx_type == "buy":
        if holding:
            # Weighted average cost: (old_q * old_cost + new_q * new_p) / (old_q + new_q)
            old_qty = holding.quantity
            old_cost = holding.average_cost
            new_qty = old_qty + data.quantity
            new_avg_cost = (old_qty * old_cost + data.quantity * data.price) / new_qty
            holding.quantity = new_qty
            holding.average_cost = new_avg_cost
            holding.current_price = data.price
            holding.current_price_as_of = tx_date
            holding.current_value = new_qty * data.price
        else:
            holding = Holding(
                id=uuid.uuid4(),
                portfolio_id=portfolio_id,
                asset_id=asset.id,
                quantity=data.quantity,
                average_cost=data.price,
                current_price=data.price,
                current_price_as_of=tx_date,
                current_value=data.quantity * data.price,
            )
            db.add(holding)

    elif tx_type == "sell":
        if holding:
            new_qty = holding.quantity - data.quantity
            if new_qty <= Decimal("0"):
                await db.delete(holding)
            else:
                holding.quantity = new_qty
                holding.current_price = data.price
                holding.current_price_as_of = tx_date
                holding.current_value = new_qty * data.price

    await db.commit()
    await db.refresh(transaction)

    return TransactionResponse(
        id=transaction.id,
        portfolio_id=transaction.portfolio_id,
        asset_id=asset.id,
        symbol=asset.symbol,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        price=transaction.price,
        fees=transaction.fees,
        transaction_date=transaction.transaction_date,
        idempotency_key=transaction.idempotency_key,
        created_at=transaction.created_at,
    )


async def list_transactions(
    db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID
) -> List[TransactionResponse]:
    """Retrieves all transaction history for a portfolio."""
    await get_portfolio_entity(db, user_id, portfolio_id)

    query = (
        select(Transaction, Asset)
        .join(Asset, Transaction.asset_id == Asset.id)
        .where(Transaction.portfolio_id == portfolio_id)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
    )
    results = (await db.execute(query)).all()

    return [
        TransactionResponse(
            id=tx.id,
            portfolio_id=tx.portfolio_id,
            asset_id=asset.id,
            symbol=asset.symbol,
            transaction_type=tx.transaction_type,
            quantity=tx.quantity,
            price=tx.price,
            fees=tx.fees,
            transaction_date=tx.transaction_date,
            idempotency_key=tx.idempotency_key,
            created_at=tx.created_at,
        )
        for tx, asset in results
    ]


# ---------------------------------------------------------------------------
# Deterministic Financial Analytics (§19, §20)
# ---------------------------------------------------------------------------

async def get_portfolio_analytics(
    db: AsyncSession, user_id: uuid.UUID, portfolio_id: uuid.UUID
) -> PortfolioAnalyticsResponse:
    """
    Computes deterministic portfolio analytics:
    Total valuation, net cost basis, absolute return, asset allocation weights,
    sector exposure distribution, concentration HHI, and XIRR rate of return.
    """
    portfolio = await get_portfolio_entity(db, user_id, portfolio_id)

    # 1. Fetch current holdings and assets
    query = (
        select(Holding, Asset)
        .join(Asset, Holding.asset_id == Asset.id)
        .where(Holding.portfolio_id == portfolio_id)
    )
    results = (await db.execute(query)).all()

    holdings_data = []
    for h, a in results:
        holdings_data.append({
            "asset_id": h.asset_id,
            "symbol": a.symbol,
            "name": a.name,
            "asset_type": a.asset_type,
            "sector": a.sector,
            "quantity": h.quantity,
            "average_cost": h.average_cost,
            "current_price": h.current_price or h.average_cost,
        })

    # 2. Pure Financial Engine calculations (§19)
    total_value = calculate_portfolio_value(holdings_data)
    total_cost = calculate_total_cost(holdings_data)
    gain_loss, gain_loss_pct = calculate_absolute_return(total_value, total_cost)

    alloc_list = calculate_allocation(holdings_data, total_value)
    allocations = [
        AllocationItem(
            asset_id=a["asset_id"],
            symbol=a["symbol"],
            name=a["name"],
            asset_type=a["asset_type"],
            value=a["value"],
            weight=a["weight"],
            weight_pct=a["weight_pct"],
        )
        for a in alloc_list
    ]

    sector_list = calculate_sector_exposure(holdings_data, total_value)
    sector_exposures = [
        SectorExposureItem(
            sector=s["sector"],
            value=s["value"],
            weight=s["weight"],
            weight_pct=s["weight_pct"],
        )
        for s in sector_list
    ]

    conc_dict = calculate_concentration(holdings_data, total_value)
    concentration = ConcentrationMetrics(
        top_1_weight=conc_dict["top_1_weight"],
        top_3_weight=conc_dict["top_3_weight"],
        top_5_weight=conc_dict["top_5_weight"],
        hhi=conc_dict["hhi"],
        concentration_level=conc_dict["concentration_level"],
    )

    # 3. Calculate XIRR from transactions
    tx_query = (
        select(Transaction)
        .where(Transaction.portfolio_id == portfolio_id)
        .order_by(Transaction.transaction_date.asc())
    )
    transactions = (await db.execute(tx_query)).scalars().all()

    xirr_rate = None
    if transactions and total_value > Decimal("0"):
        cash_flows = []
        for tx in transactions:
            # Buys represent cash outflows (negative)
            if tx.transaction_type == "buy":
                cash_flows.append((tx.transaction_date, -(tx.quantity * tx.price + tx.fees)))
            elif tx.transaction_type == "sell":
                cash_flows.append((tx.transaction_date, (tx.quantity * tx.price - tx.fees)))
            elif tx.transaction_type == "dividend":
                cash_flows.append((tx.transaction_date, (tx.quantity * tx.price)))

        # Terminal valuation as of today (positive inflow)
        if cash_flows:
            cash_flows.append((datetime.now(timezone.utc), total_value))
            xirr_rate = calculate_xirr(cash_flows)

    return PortfolioAnalyticsResponse(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        is_virtual=portfolio.is_virtual,
        base_currency=portfolio.base_currency,
        total_value=total_value,
        total_cost=total_cost,
        unrealized_gain_loss=gain_loss,
        unrealized_gain_loss_pct=gain_loss_pct,
        holdings_count=len(holdings_data),
        allocations=allocations,
        sector_exposures=sector_exposures,
        concentration=concentration,
        annualized_return_xirr=xirr_rate,
    )
