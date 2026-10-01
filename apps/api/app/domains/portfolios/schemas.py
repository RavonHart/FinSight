import uuid
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class AssetBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=255)
    asset_type: str = Field("stock", description="stock, etf, bond, mutual_fund, cash")
    exchange: Optional[str] = None
    currency: str = "USD"
    sector: Optional[str] = None
    industry: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    base_currency: str = Field("USD", min_length=3, max_length=10)
    portfolio_type: str = Field("manual", description="'manual' or 'virtual'")
    is_virtual: bool = False


class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    base_currency: Optional[str] = Field(None, min_length=3, max_length=10)


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    base_currency: str
    portfolio_type: str
    is_virtual: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HoldingCreate(BaseModel):
    symbol: str = Field(..., description="Asset ticker symbol, e.g. AAPL, VTI")
    name: Optional[str] = None
    asset_type: Optional[str] = "stock"
    sector: Optional[str] = None
    quantity: Decimal = Field(..., gt=0, description="Share quantity held")
    average_cost: Decimal = Field(..., ge=0, description="Cost basis per share (USD)")
    current_price: Optional[Decimal] = Field(None, ge=0, description="Current market price per share")


class HoldingUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0)
    average_cost: Optional[Decimal] = Field(None, ge=0)
    current_price: Optional[Decimal] = Field(None, ge=0)


class HoldingResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    asset_id: uuid.UUID
    symbol: str
    name: str
    asset_type: str
    sector: Optional[str] = None
    quantity: Decimal
    average_cost: Decimal
    current_price: Optional[Decimal] = None
    current_price_as_of: Optional[datetime] = None
    current_value: Optional[Decimal] = None
    unrealized_gain_loss: Optional[Decimal] = None
    unrealized_gain_loss_pct: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    symbol: str = Field(..., description="Asset ticker symbol, e.g. AAPL")
    transaction_type: str = Field(..., description="'buy', 'sell', 'dividend', 'split', 'fee_adjustment'")
    quantity: Decimal = Field(..., gt=0, description="Transaction quantity")
    price: Decimal = Field(..., ge=0, description="Transaction unit price")
    fees: Decimal = Field(Decimal("0.00"), ge=0, description="Commission / transaction fees")
    transaction_date: Optional[datetime] = None
    idempotency_key: Optional[str] = Field(None, max_length=128, description="Client idempotency key (§45)")


class TransactionResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    asset_id: uuid.UUID
    symbol: str
    transaction_type: str
    quantity: Decimal
    price: Decimal
    fees: Decimal
    transaction_date: datetime
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AllocationItem(BaseModel):
    asset_id: Optional[uuid.UUID] = None
    symbol: str
    name: str
    asset_type: str
    value: Decimal
    weight: Decimal
    weight_pct: Decimal


class SectorExposureItem(BaseModel):
    sector: str
    value: Decimal
    weight: Decimal
    weight_pct: Decimal


class ConcentrationMetrics(BaseModel):
    top_1_weight: Decimal
    top_3_weight: Decimal
    top_5_weight: Decimal
    hhi: Decimal
    concentration_level: str


class PortfolioAnalyticsResponse(BaseModel):
    portfolio_id: uuid.UUID
    portfolio_name: str
    is_virtual: bool
    base_currency: str
    total_value: Decimal
    total_cost: Decimal
    unrealized_gain_loss: Decimal
    unrealized_gain_loss_pct: Optional[Decimal] = None
    holdings_count: int
    allocations: List[AllocationItem]
    sector_exposures: List[SectorExposureItem]
    concentration: ConcentrationMetrics
    annualized_return_xirr: Optional[Decimal] = None
