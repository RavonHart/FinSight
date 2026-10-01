import uuid
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class SimulationRequest(BaseModel):
    portfolio_id: Optional[uuid.UUID] = Field(None, description="Optional portfolio ID to seed initial capital")
    initial_capital: Decimal = Field(Decimal("10000.00"), ge=0, description="Initial investment balance")
    monthly_contribution: Decimal = Field(Decimal("500.00"), ge=0, description="Monthly recurring contribution")
    duration_years: int = Field(10, ge=1, le=50, description="Simulation duration in years")
    annual_return_pct: Decimal = Field(Decimal("7.0"), ge=-50, le=100, description="Expected annual rate of return")
    annual_inflation_pct: Decimal = Field(Decimal("2.5"), ge=-10, le=50, description="Expected annual inflation rate")
    annual_fee_pct: Decimal = Field(Decimal("0.25"), ge=0, le=10, description="Annual asset management / expense fee")
    annual_withdrawal: Decimal = Field(Decimal("0.00"), ge=0, description="Annual withdrawal or decumulation amount")


class YearlySnapshot(BaseModel):
    year: int
    starting_balance: Decimal
    contributions: Decimal
    withdrawals: Decimal
    investment_growth: Decimal
    fees_paid: Decimal
    ending_nominal_value: Decimal
    ending_real_value: Decimal


class ScenarioResult(BaseModel):
    engine_version: str
    duration_years: int
    initial_capital: Decimal
    total_contributions: Decimal
    total_withdrawals: Decimal
    total_fees_paid: Decimal
    nominal_ending_value: Decimal
    real_ending_value: Decimal
    total_gain: Decimal
    is_depleted: bool
    depletion_year: Optional[int] = None
    yearly_snapshots: List[YearlySnapshot]


class ScenarioDetail(BaseModel):
    label: str
    assumptions: Dict[str, float]
    result: ScenarioResult


class SimulationRunResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    portfolio_id: Optional[uuid.UUID] = None
    simulation_type: str
    engine_version: str
    input_json: Dict[str, Any]
    result_json: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
