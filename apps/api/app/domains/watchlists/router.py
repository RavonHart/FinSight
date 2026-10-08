import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.db.models.users import User
from app.domains.watchlists.schemas import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistItemCreate,
    WatchlistItemResponse,
    WatchlistScanResponse,
    WatchlistResponse,
    WatchlistDetailResponse,
    NotificationResponse,
    NotificationSummaryResponse,
    NotificationMarkReadRequest,
)
from app.domains.watchlists.service import (
    create_watchlist,
    list_watchlists,
    get_watchlist_detail,
    update_watchlist,
    delete_watchlist,
    add_watchlist_item,
    remove_watchlist_item,
    trigger_watchlist_scan,
    list_user_notifications,
    mark_notifications_read,
)

watchlists_router = APIRouter(prefix="/watchlists", tags=["watchlists"])
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])


# ---------------------------------------------------------------------------
# Watchlists Endpoints
# ---------------------------------------------------------------------------

@watchlists_router.get(
    "",
    response_model=List[WatchlistResponse],
    summary="List user watchlists",
)
async def list_user_watchlists_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all watchlists created by the authenticated user with item counts and latest scan."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_watchlists(db, user_uuid)


@watchlists_router.post(
    "",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new watchlist",
)
async def create_watchlist_endpoint(
    data: WatchlistCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new watchlist for automated scanning (§10, §38)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await create_watchlist(db, user_uuid, data)


@watchlists_router.get(
    "/{watchlist_id}",
    response_model=WatchlistDetailResponse,
    summary="Get watchlist details with items and scan history",
)
async def get_watchlist_detail_endpoint(
    watchlist_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns full watchlist structure including tracked assets and historical scan results."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await get_watchlist_detail(db, user_uuid, watchlist_id)


@watchlists_router.patch(
    "/{watchlist_id}",
    response_model=WatchlistResponse,
    summary="Update watchlist settings",
)
async def update_watchlist_endpoint(
    watchlist_id: uuid.UUID,
    data: WatchlistUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates watchlist name or Celery scan schedule."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await update_watchlist(db, user_uuid, watchlist_id, data)


@watchlists_router.delete(
    "/{watchlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete watchlist",
)
async def delete_watchlist_endpoint(
    watchlist_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes watchlist and cascading items and scan findings."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    await delete_watchlist(db, user_uuid, watchlist_id)
    return None


@watchlists_router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an asset/ticker to watchlist",
)
async def add_watchlist_item_endpoint(
    watchlist_id: uuid.UUID,
    data: WatchlistItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Adds a stock or ETF to the specified watchlist (§38)."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await add_watchlist_item(db, user_uuid, watchlist_id, ticker=data.ticker, asset_id=data.asset_id)


@watchlists_router.delete(
    "/{watchlist_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item from watchlist",
)
async def remove_watchlist_item_endpoint(
    watchlist_id: uuid.UUID,
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Removes a tracked asset from the watchlist."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    await remove_watchlist_item(db, user_uuid, watchlist_id, item_id)
    return None


@watchlists_router.post(
    "/{watchlist_id}/scan",
    response_model=WatchlistScanResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an automated market scan for the watchlist",
)
async def trigger_watchlist_scan_endpoint(
    watchlist_id: uuid.UUID,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    run_sync: bool = Query(False, description="Run synchronously for immediate testing"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers a background watchlist scan job.
    Enforces scan idempotency and prevents concurrent duplicate execution (§10, §38).
    """
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await trigger_watchlist_scan(
        db, user_uuid, watchlist_id, idempotency_key=idempotency_key, run_sync=run_sync
    )


# ---------------------------------------------------------------------------
# Notifications Endpoints (§10, §38)
# ---------------------------------------------------------------------------

@notifications_router.get(
    "",
    response_model=NotificationSummaryResponse,
    summary="List user notifications",
)
async def list_notifications_endpoint(
    unread_only: bool = Query(False, description="Filter to only unread notifications"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists notifications and unread alert count for the user."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    return await list_user_notifications(db, user_uuid, unread_only=unread_only, limit=limit)


@notifications_router.post(
    "/mark-read",
    summary="Mark notifications as read",
)
async def mark_notifications_read_endpoint(
    data: Optional[NotificationMarkReadRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Marks specified or all unread notifications as read."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    notification_ids = data.notification_ids if data else None
    count = await mark_notifications_read(db, user_uuid, notification_ids=notification_ids)
    return {"status": "ok", "marked_read_count": count}


@notifications_router.patch(
    "/{notification_id}/read",
    summary="Mark single notification as read",
)
async def mark_single_notification_read_endpoint(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Marks a specific notification as read."""
    user_uuid = current_user.id if isinstance(current_user.id, uuid.UUID) else uuid.UUID(str(current_user.id))
    count = await mark_notifications_read(db, user_uuid, notification_ids=[notification_id])
    return {"status": "ok", "marked_read_count": count}
