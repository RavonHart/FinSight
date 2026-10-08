import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Watchlists & Items
# ---------------------------------------------------------------------------

class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Display name for the watchlist")
    scan_enabled: bool = Field(default=True, description="Enable automated background scanning via Celery Beat")
    scan_frequency: Optional[str] = Field(default="daily", description="'daily' or 'weekly'")


class WatchlistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    scan_enabled: Optional[bool] = None
    scan_frequency: Optional[str] = None


class WatchlistItemCreate(BaseModel):
    ticker: Optional[str] = Field(None, description="Asset ticker symbol, e.g. 'NVDA', 'AAPL', 'MSFT'")
    asset_id: Optional[uuid.UUID] = Field(None, description="Existing asset UUID")


class WatchlistItemResponse(BaseModel):
    id: uuid.UUID
    watchlist_id: uuid.UUID
    asset_id: uuid.UUID
    ticker: str
    name: str
    asset_class: str
    current_price: Optional[Decimal] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Watchlist Scans & Findings
# ---------------------------------------------------------------------------

class WatchlistScanFinding(BaseModel):
    asset_id: uuid.UUID
    ticker: str
    name: str
    signal_type: str = Field(..., description="'momentum_shift', 'valuation_compression', 'drawdown_alert', 'volatility_spike'")
    severity: str = Field(..., description="'low', 'medium', 'high'")
    summary: str
    details: str
    metrics: Dict[str, Any] = Field(default_factory=dict)


class WatchlistScanResponse(BaseModel):
    id: uuid.UUID
    watchlist_id: uuid.UUID
    status: str
    findings_count: int
    findings: List[WatchlistScanFinding]
    error_message: Optional[str] = None
    idempotency_key: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class WatchlistResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    scan_enabled: bool
    scan_frequency: Optional[str] = None
    items_count: int
    latest_scan: Optional[WatchlistScanResponse] = None
    created_at: datetime


class WatchlistDetailResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    scan_enabled: bool
    scan_frequency: Optional[str] = None
    items: List[WatchlistItemResponse]
    scans: List[WatchlistScanResponse]
    created_at: datetime


# ---------------------------------------------------------------------------
# Notifications (§10, §38)
# ---------------------------------------------------------------------------

class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    title: str
    body: str
    related_resource_type: Optional[str] = None
    related_resource_id: Optional[uuid.UUID] = None
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime


class NotificationSummaryResponse(BaseModel):
    total_unread: int
    notifications: List[NotificationResponse]


class NotificationMarkReadRequest(BaseModel):
    notification_ids: Optional[List[uuid.UUID]] = Field(None, description="Optional list of notification UUIDs to mark read. If null or empty, marks all unread.")
