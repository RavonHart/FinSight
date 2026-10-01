import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from app.db.models.simulations import SimulationRun
from app.db.models.portfolios import Portfolio, Holding
from app.domains.simulations.schemas import SimulationRequest
from app.finance.simulation import run_multi_scenario_simulation
from app.finance.engine import calculate_portfolio_value


def _serialize_decimals(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _serialize_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_decimals(x) for x in obj]
    return obj


async def execute_and_persist_simulation(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: SimulationRequest,
) -> SimulationRun:
    """
    Executes multi-scenario deterministic simulation with pinned engine version
    and durably persists the reproducible run (§10, §20, §28, §58).
    """
    initial_cap = data.initial_capital

    # If portfolio_id is provided, verify ownership and optionally seed initial capital
    if data.portfolio_id:
        p_stmt = select(Portfolio).where(
            Portfolio.id == data.portfolio_id,
            Portfolio.user_id == user_id,
        )
        p_res = await db.execute(p_stmt)
        portfolio = p_res.scalar_one_or_none()
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {data.portfolio_id} not found or access denied.",
            )

        # If initial_capital was 0, calculate current portfolio value
        if initial_cap <= Decimal("0"):
            h_stmt = select(Holding).where(Holding.portfolio_id == portfolio.id)
            h_res = await db.execute(h_stmt)
            holdings = h_res.scalars().all()
            h_dicts = [
                {
                    "quantity": h.quantity,
                    "current_price": h.current_price,
                    "average_cost": h.average_cost,
                }
                for h in holdings
            ]
            initial_cap = calculate_portfolio_value(h_dicts)

    # Execute deterministic multi-scenario forward modeling
    results = run_multi_scenario_simulation(
        initial_capital=initial_cap,
        monthly_contribution=data.monthly_contribution,
        duration_years=data.duration_years,
        base_annual_return=data.annual_return_pct,
        base_inflation=data.annual_inflation_pct,
        annual_fee=data.annual_fee_pct,
        annual_withdrawal=data.annual_withdrawal,
    )

    input_payload = {
        "portfolio_id": str(data.portfolio_id) if data.portfolio_id else None,
        "initial_capital": float(initial_cap),
        "monthly_contribution": float(data.monthly_contribution),
        "duration_years": data.duration_years,
        "annual_return_pct": float(data.annual_return_pct),
        "annual_inflation_pct": float(data.annual_inflation_pct),
        "annual_fee_pct": float(data.annual_fee_pct),
        "annual_withdrawal": float(data.annual_withdrawal),
    }

    serialized_results = _serialize_decimals(results)

    sim_run = SimulationRun(
        id=uuid.uuid4(),
        user_id=user_id,
        portfolio_id=data.portfolio_id,
        simulation_type="compound_growth_scenarios",
        engine_version="financial-engine-v1",
        input_json=input_payload,
        result_json=serialized_results,
        created_at=datetime.now(timezone.utc),
    )

    db.add(sim_run)
    await db.commit()
    await db.refresh(sim_run)

    return sim_run


async def get_simulation_run(
    db: AsyncSession,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
) -> SimulationRun:
    """Retrieves a single simulation run verifying tenant user isolation (§11, §30)."""
    stmt = select(SimulationRun).where(
        SimulationRun.id == run_id,
        SimulationRun.user_id == user_id,
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation run {run_id} not found or access denied.",
        )
    return run


async def list_simulation_runs(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
) -> List[SimulationRun]:
    """Lists historical simulation runs for user."""
    stmt = (
        select(SimulationRun)
        .where(SimulationRun.user_id == user_id)
        .order_by(desc(SimulationRun.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
